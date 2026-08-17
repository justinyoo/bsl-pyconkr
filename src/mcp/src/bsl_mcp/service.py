"""MCP 도구용 입력 검증과 NEIS 응답 정규화."""

from __future__ import annotations

import re
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from math import isfinite
from typing import Any
from zoneinfo import ZoneInfo

from bsl_mcp.client import SchoolAndMealClient
from bsl_mcp.exceptions import (
    MealsNotFoundError,
    NeisResponseError,
    SchoolNotFoundError,
)
from bsl_mcp.models import Meal, School, SchoolMealsResult, SchoolSearchResult

_BR_PATTERN = re.compile(r"<br\s*/?>", re.IGNORECASE)
_KST = ZoneInfo("Asia/Seoul")


def _required_text(row: dict[str, Any], key: str) -> str:
    value = row.get(key)
    if not isinstance(value, (str, int)) or isinstance(value, bool):
        raise NeisResponseError
    text = str(value).strip()
    if not text:
        raise NeisResponseError
    return text


def _optional_text(row: dict[str, Any], key: str) -> str | None:
    value = row.get(key)
    if value is None:
        return None
    if not isinstance(value, (str, int)) or isinstance(value, bool):
        raise NeisResponseError
    return str(value).strip() or None


def _school(row: dict[str, Any]) -> School:
    return School(
        school_code=_required_text(row, "SD_SCHUL_CODE"),
        education_office_code=_required_text(row, "ATPT_OFCDC_SC_CODE"),
        school_name=_required_text(row, "SCHUL_NM"),
        education_office_name=_required_text(row, "ATPT_OFCDC_SC_NM"),
        location_name=_optional_text(row, "LCTN_SC_NM"),
        school_type=_optional_text(row, "SCHUL_KND_SC_NM"),
    )


def _split_lines(value: object) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, str):
        raise NeisResponseError
    return [part for raw in _BR_PATTERN.split(value) if (part := raw.strip())]


def _serving_count(value: object) -> int | None:
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value if value >= 0 else None
    if isinstance(value, float):
        if isfinite(value) and value.is_integer() and value >= 0:
            return int(value)
        return None
    if not isinstance(value, str):
        return None
    match = re.search(r"-?\d[\d,]*(?:\.\d+)?", value)
    if match is None:
        return None
    try:
        number = Decimal(match.group().replace(",", ""))
    except InvalidOperation:
        return None
    if number >= 0 and number == number.to_integral_value():
        return int(number)
    return None


def _meal(row: dict[str, Any]) -> Meal:
    if _required_text(row, "MMEAL_SC_CODE") != "2":
        raise NeisResponseError
    try:
        meal_date = datetime.strptime(
            _required_text(row, "MLSV_YMD"), "%Y%m%d"
        ).date()
    except ValueError as exc:
        raise NeisResponseError from exc
    return Meal(
        date=meal_date,
        dishes=_split_lines(row.get("DDISH_NM")),
        origins=_split_lines(row.get("ORPLC_INFO")),
        nutrition=_split_lines(row.get("NTR_INFO")),
        calories=_optional_text(row, "CAL_INFO"),
        serving_count=_serving_count(row.get("MLSV_FGR")),
    )


def _validate_dates(from_date: date, to_date: date) -> None:
    today = datetime.now(tz=_KST).date()
    if today.month == 1:
        earliest = date(today.year - 1, 12, 1)
    else:
        earliest = date(today.year, today.month - 1, 1)
    if to_date < from_date:
        raise ValueError("종료일은 시작일보다 빠를 수 없습니다.")
    if from_date < earliest:
        raise ValueError(
            f"시작일은 직전 달 1일({earliest.isoformat()})보다 빠를 수 없습니다."
        )
    if to_date > today:
        raise ValueError("종료일은 오늘보다 늦을 수 없습니다.")


async def search_schools(
    client: SchoolAndMealClient, school_name: str
) -> SchoolSearchResult:
    query = "".join(school_name.split())
    if len(query) < 2:
        raise ValueError("학교 이름은 공백을 제외하고 2자 이상 입력해야 합니다.")
    rows = await client.search_schools(query)
    if not rows:
        raise SchoolNotFoundError
    schools = [_school(row) for row in rows]
    return SchoolSearchResult(schools=schools, total=len(schools))


async def get_school_lunches(
    client: SchoolAndMealClient,
    *,
    education_office_code: str,
    school_code: str,
    from_date: date,
    to_date: date,
) -> SchoolMealsResult:
    _validate_dates(from_date, to_date)
    if not education_office_code.strip() or not school_code.strip():
        raise ValueError("교육청 코드와 학교 코드를 모두 입력해야 합니다.")
    school_rows = await client.get_school(
        education_office_code=education_office_code.strip(),
        school_code=school_code.strip(),
    )
    if not school_rows:
        raise SchoolNotFoundError
    school = _school(school_rows[0])
    rows = await client.get_lunches(
        education_office_code=school.education_office_code,
        school_code=school.school_code,
        from_ymd=from_date.strftime("%Y%m%d"),
        to_ymd=to_date.strftime("%Y%m%d"),
    )
    if not rows:
        raise MealsNotFoundError
    meals = sorted((_meal(row) for row in rows), key=lambda item: item.date)
    if any(meal.date < from_date or meal.date > to_date for meal in meals):
        raise NeisResponseError
    return SchoolMealsResult(
        school=school,
        from_date=from_date,
        to_date=to_date,
        meals=meals,
    )
