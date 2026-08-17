"""급식 정보 정규화 단위 테스트. 네트워크를 사용하지 않는다."""

from __future__ import annotations

from datetime import date

import pytest

from bsl_api.errors import UpstreamError
from bsl_api.services.meals import (
    _iso_to_ymd,
    _parse_calories,
    _parse_serving_count,
    _split_br,
    _to_meal,
    _ymd_to_iso,
)


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("현미밥<br/>미역국<br/>닭갈비", ["현미밥", "미역국", "닭갈비"]),
        ("현미밥<br>미역국", ["현미밥", "미역국"]),
        ("현미밥<br />미역국", ["현미밥", "미역국"]),
        ("현미밥<BR/>미역국<Br>닭갈비", ["현미밥", "미역국", "닭갈비"]),
        ("단일 메뉴", ["단일 메뉴"]),
        ("", []),
        (None, []),
    ],
)
def test_split_br_handles_all_variants(
    raw: str | None, expected: list[str]
) -> None:
    assert _split_br(raw) == expected


def test_split_br_drops_empty_segments() -> None:
    assert _split_br("첫줄<br/><br/>둘째줄") == ["첫줄", "둘째줄"]


@pytest.mark.parametrize(
    ("raw", "expected"),
    [("742.3 Kcal", "742.3 Kcal"), ("  700 Kcal  ", "700 Kcal"), (None, None), ("", None)],
)
def test_parse_calories(raw: str | None, expected: str | None) -> None:
    assert _parse_calories(raw) == expected


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("530", 530),
        ("530명", 530),
        ("530.0명", 530),
        ("1,230명", 1230),
        (530, 530),
        (530.0, 530),
        (530.5, None),
        (None, None),
        ("", None),
        ("없음", None),
    ],
)
def test_parse_serving_count(
    raw: str | int | float | None, expected: int | None
) -> None:
    assert _parse_serving_count(raw) == expected


def test_ymd_iso_roundtrip() -> None:
    assert _ymd_to_iso("20260817") == date(2026, 8, 17)
    assert _iso_to_ymd(date(2026, 8, 17)) == "20260817"


def test_to_meal_normalizes_row() -> None:
    row = {
        "MMEAL_SC_CODE": "2",
        "MLSV_YMD": "20260817",
        "DDISH_NM": "현미밥<br/>미역국",
        "ORPLC_INFO": "쌀: 국내산",
        "NTR_INFO": "탄수화물(g): 92.1<br/>단백질(g): 31.4",
        "CAL_INFO": "742.3 Kcal",
        "MLSV_FGR": "530",
    }
    meal = _to_meal(row)
    assert meal.date == date(2026, 8, 17)
    assert meal.dishes == ["현미밥", "미역국"]
    assert meal.origins == ["쌀: 국내산"]
    assert meal.nutrition == ["탄수화물(g): 92.1", "단백질(g): 31.4"]
    assert meal.calories == "742.3 Kcal"
    assert meal.serving_count == 530


def test_to_meal_rejects_non_lunch_code() -> None:
    row = {
        "MMEAL_SC_CODE": "1",
        "MLSV_YMD": "20260817",
        "DDISH_NM": "토스트",
    }
    with pytest.raises(UpstreamError):
        _to_meal(row)


def test_to_meal_handles_missing_optional_fields() -> None:
    row = {
        "MMEAL_SC_CODE": "2",
        "MLSV_YMD": "20260817",
        "DDISH_NM": "현미밥",
    }
    meal = _to_meal(row)
    assert meal.origins == []
    assert meal.nutrition == []
    assert meal.calories is None
    assert meal.serving_count is None
