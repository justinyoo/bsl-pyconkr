"""중식 조회 유스케이스: 날짜 검증, NEIS 호출과 내부 모델 정규화."""

from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation
from datetime import date, datetime
from math import isfinite
from typing import Any

from bsl_api.clients.exceptions import (
    NeisAuthenticationError,
    NeisRateLimitedError,
    NeisUnavailableError,
    NeisUpstreamError,
)
from bsl_api.clients.base import SchoolAndMealClient
from bsl_api.errors import (
    RateLimitedError,
    SchoolNotFoundError,
    UpstreamError,
    UpstreamUnavailableError,
)
from bsl_api.models.schemas import Meal, MealRangeResponse, SelectedSchool
from bsl_api.services.dates import validate_date_range

_BR_PATTERN = re.compile(r"<br\s*/?>", re.IGNORECASE)
_LUNCH_CODE = "2"


def _split_br(value: str | None) -> list[str]:
    if not value:
        return []
    parts = [part.strip() for part in _BR_PATTERN.split(value)]
    return [part for part in parts if part]


def _parse_calories(value: str | None) -> str | None:
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None


def _parse_serving_count(value: str | int | float | None) -> int | None:
    if value is None:
        return None

    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value if value >= 0 else None
    if isinstance(value, float):
        if not isfinite(value) or not value.is_integer() or value < 0:
            return None
        return int(value)

    match = re.search(r"-?\d[\d,]*(?:\.\d+)?", value)
    if match is None:
        return None
    try:
        number = Decimal(match.group().replace(",", ""))
    except InvalidOperation:
        return None
    if number < 0 or number != number.to_integral_value():
        return None
    return int(number)


def _ymd_to_iso(value: str) -> date:
    return datetime.strptime(value, "%Y%m%d").date()


def _iso_to_ymd(value: date) -> str:
    return value.strftime("%Y%m%d")


def _to_selected_school(row: dict[str, Any]) -> SelectedSchool:
    return SelectedSchool(
        school_code=str(row["SD_SCHUL_CODE"]),
        education_office_code=str(row["ATPT_OFCDC_SC_CODE"]),
        school_name=str(row["SCHUL_NM"]),
        education_office_name=str(row["ATPT_OFCDC_SC_NM"]),
    )


def _to_meal(row: dict[str, Any]) -> Meal:
    meal_code = str(row.get("MMEAL_SC_CODE", ""))
    if meal_code != _LUNCH_CODE:
        raise UpstreamError("NEIS가 중식이 아닌 급식 정보를 반환했습니다.")
    return Meal(
        date=_ymd_to_iso(str(row["MLSV_YMD"])),
        dishes=_split_br(row.get("DDISH_NM")),
        origins=_split_br(row.get("ORPLC_INFO")),
        nutrition=_split_br(row.get("NTR_INFO")),
        calories=_parse_calories(row.get("CAL_INFO")),
        serving_count=_parse_serving_count(row.get("MLSV_FGR")),
    )


async def get_school_meals(
    client: SchoolAndMealClient,
    *,
    school_code: str,
    office_code: str,
    from_date: date,
    to_date: date,
) -> MealRangeResponse:
    """학교와 날짜 범위를 검증하고 중식 정보를 조회한다."""

    validate_date_range(from_date, to_date)

    try:
        school_rows = await client.get_school(
            office_code=office_code, school_code=school_code
        )
    except NeisRateLimitedError as exc:
        raise RateLimitedError(str(exc)) from exc
    except NeisAuthenticationError as exc:
        raise UpstreamError(str(exc)) from exc
    except NeisUpstreamError as exc:
        raise UpstreamError(str(exc)) from exc
    except NeisUnavailableError as exc:
        raise UpstreamUnavailableError(str(exc)) from exc

    if not school_rows:
        raise SchoolNotFoundError()

    school = _to_selected_school(school_rows[0])

    try:
        meal_rows = await client.get_lunches(
            office_code=office_code,
            school_code=school_code,
            from_ymd=_iso_to_ymd(from_date),
            to_ymd=_iso_to_ymd(to_date),
        )
    except NeisRateLimitedError as exc:
        raise RateLimitedError(str(exc)) from exc
    except NeisAuthenticationError as exc:
        raise UpstreamError(str(exc)) from exc
    except NeisUpstreamError as exc:
        raise UpstreamError(str(exc)) from exc
    except NeisUnavailableError as exc:
        raise UpstreamUnavailableError(str(exc)) from exc

    meals = sorted((_to_meal(row) for row in meal_rows), key=lambda meal: meal.date)

    return MealRangeResponse(school=school, from_=from_date, to=to_date, meals=meals)
