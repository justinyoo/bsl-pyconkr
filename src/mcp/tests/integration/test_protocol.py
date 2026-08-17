"""MCP 프로토콜 도구 조회·호출 통합 테스트."""

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import pytest
from mcp.client.session import ClientSession
from mcp.types import TextContent


@pytest.mark.anyio
async def test_lists_expected_tools(client_session: ClientSession) -> None:
    result = await client_session.list_tools()

    assert {tool.name for tool in result.tools} == {
        "search_schools",
        "get_school_lunches",
    }
    search_tool = next(tool for tool in result.tools if tool.name == "search_schools")
    assert search_tool.outputSchema is not None


@pytest.mark.anyio
async def test_calls_school_search_tool(client_session: ClientSession) -> None:
    result = await client_session.call_tool(
        "search_schools", {"school_name": "서울고정"}
    )

    assert result.isError is False
    assert result.structuredContent is not None
    assert result.structuredContent["total"] == 1
    assert result.structuredContent["schools"][0]["school_code"] == "7010001"


@pytest.mark.anyio
async def test_calls_lunch_tool(client_session: ClientSession) -> None:
    today = datetime.now(tz=ZoneInfo("Asia/Seoul")).date()
    result = await client_session.call_tool(
        "get_school_lunches",
        {
            "education_office_code": "B10",
            "school_code": "7010001",
            "from_date": (today - timedelta(days=1)).isoformat(),
            "to_date": today.isoformat(),
        },
    )

    assert result.isError is False
    assert result.structuredContent is not None
    assert len(result.structuredContent["meals"]) == 2
    assert all(
        meal["meal_type"] == "lunch"
        for meal in result.structuredContent["meals"]
    )


@pytest.mark.anyio
async def test_returns_standard_tool_error_for_empty_search(
    client_session: ClientSession,
) -> None:
    result = await client_session.call_tool(
        "search_schools", {"school_name": "없는학교"}
    )

    assert result.isError is True
    assert isinstance(result.content[0], TextContent)
    assert result.content[0].text.endswith(
        "조건과 일치하는 학교를 찾을 수 없습니다."
    )
