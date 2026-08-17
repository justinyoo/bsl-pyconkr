"""조회 가능 날짜 범위 계산과 검증.

허용 범위는 한국 표준시(KST) 기준 직전 달 1일부터 오늘까지다.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from zoneinfo import ZoneInfo

from bsl_api.errors import InvalidDateRangeError

KST = ZoneInfo("Asia/Seoul")


def today_kst() -> date:
    """한국 표준시 기준 오늘 날짜를 반환한다."""

    return datetime.now(tz=KST).date()


def first_day_of_previous_month(reference: date) -> date:
    """기준일이 속한 달의 직전 달 1일을 반환한다."""

    year, month = reference.year, reference.month
    if month == 1:
        return date(year - 1, 12, 1)
    return date(year, month - 1, 1)


@dataclass(frozen=True)
class AllowedRange:
    start: date
    end: date


def allowed_range(reference: date | None = None) -> AllowedRange:
    """조회 가능한 날짜 범위(직전 달 1일 ~ 오늘)를 반환한다."""

    today = reference if reference is not None else today_kst()
    return AllowedRange(start=first_day_of_previous_month(today), end=today)


def validate_date_range(
    from_date: date, to_date: date, *, reference: date | None = None
) -> None:
    """날짜 범위가 역순이거나 허용 범위를 벗어나면 예외를 발생시킨다.

    `reference`는 "오늘"을 고정해 테스트를 결정적으로 만들 때 사용한다.
    """

    bounds = allowed_range(reference)
    errors: dict[str, list[str]] = {}

    if to_date < from_date:
        errors.setdefault("to", []).append("종료일은 시작일보다 빠를 수 없습니다.")
    if from_date < bounds.start:
        errors.setdefault("from", []).append(
            f"시작일은 {bounds.start.isoformat()} 이후여야 합니다."
        )
    if to_date > bounds.end:
        errors.setdefault("to", []).append(
            f"종료일은 {bounds.end.isoformat()} 이전이어야 합니다."
        )

    if errors:
        raise InvalidDateRangeError(
            "조회 기간은 직전 달 1일부터 오늘까지의 범위여야 하며, "
            "종료일은 시작일보다 빠를 수 없습니다.",
            errors=errors,
        )
