"""날짜 범위 검증 경계값 단위 테스트. 네트워크를 사용하지 않는다."""

from __future__ import annotations

from datetime import date

import pytest

from bsl_api.errors import InvalidDateRangeError
from bsl_api.services.dates import (
    allowed_range,
    first_day_of_previous_month,
    validate_date_range,
)

FIXED_TODAY = date(2026, 8, 17)


@pytest.mark.parametrize(
    ("reference", "expected"),
    [
        (date(2026, 8, 17), date(2026, 7, 1)),
        (date(2026, 1, 15), date(2025, 12, 1)),
        (date(2026, 3, 1), date(2026, 2, 1)),
    ],
)
def test_first_day_of_previous_month(reference: date, expected: date) -> None:
    assert first_day_of_previous_month(reference) == expected


def test_allowed_range_matches_previous_month_start_and_today() -> None:
    bounds = allowed_range(FIXED_TODAY)
    assert bounds.start == date(2026, 7, 1)
    assert bounds.end == FIXED_TODAY


def test_validate_date_range_accepts_allowed_start_boundary() -> None:
    bounds = allowed_range(FIXED_TODAY)
    validate_date_range(bounds.start, bounds.start, reference=FIXED_TODAY)


def test_validate_date_range_accepts_today_boundary() -> None:
    bounds = allowed_range(FIXED_TODAY)
    validate_date_range(bounds.start, bounds.end, reference=FIXED_TODAY)


def test_validate_date_range_rejects_day_before_allowed_start() -> None:
    one_day_before_start = date(2026, 6, 30)
    with pytest.raises(InvalidDateRangeError):
        validate_date_range(
            one_day_before_start, FIXED_TODAY, reference=FIXED_TODAY
        )


def test_validate_date_range_rejects_day_after_today() -> None:
    tomorrow = date(2026, 8, 18)
    with pytest.raises(InvalidDateRangeError):
        validate_date_range(FIXED_TODAY, tomorrow, reference=FIXED_TODAY)


def test_validate_date_range_rejects_reversed_range() -> None:
    with pytest.raises(InvalidDateRangeError):
        validate_date_range(
            date(2026, 8, 10), date(2026, 8, 5), reference=FIXED_TODAY
        )
