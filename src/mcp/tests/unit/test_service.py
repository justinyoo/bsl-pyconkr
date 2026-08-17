"""도구 서비스 입력 검증과 정규화 테스트."""

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import pytest

from bsl_mcp.client import FixtureNeisClient
from bsl_mcp.exceptions import SchoolNotFoundError
from bsl_mcp.service import get_school_lunches, search_schools


@pytest.mark.anyio
async def test_search_schools_normalizes_identifiers() -> None:
    result = await search_schools(FixtureNeisClient(), "서울 고정")

    assert result.total == 1
    assert result.schools[0].school_code == "7010001"
    assert result.schools[0].education_office_code == "B10"


@pytest.mark.anyio
async def test_search_schools_rejects_short_query() -> None:
    with pytest.raises(ValueError, match="2자 이상"):
        await search_schools(FixtureNeisClient(), "서 ")


@pytest.mark.anyio
async def test_search_schools_reports_no_results() -> None:
    with pytest.raises(SchoolNotFoundError):
        await search_schools(FixtureNeisClient(), "없는학교")


@pytest.mark.anyio
async def test_get_school_lunches_normalizes_and_sorts_meals() -> None:
    today = datetime.now(tz=ZoneInfo("Asia/Seoul")).date()
    yesterday = today - timedelta(days=1)
    result = await get_school_lunches(
        FixtureNeisClient(),
        education_office_code="B10",
        school_code="7010001",
        from_date=yesterday,
        to_date=today,
    )

    assert [meal.date for meal in result.meals] == [yesterday, today]
    assert result.meals[0].dishes == ["현미밥", "된장찌개", "제육볶음"]
    assert result.meals[0].serving_count == 450


@pytest.mark.anyio
async def test_get_school_lunches_rejects_reversed_range() -> None:
    today = datetime.now(tz=ZoneInfo("Asia/Seoul")).date()
    with pytest.raises(ValueError, match="빠를 수 없습니다"):
        await get_school_lunches(
            FixtureNeisClient(),
            education_office_code="B10",
            school_code="7010001",
            from_date=today,
            to_date=today - timedelta(days=1),
        )
