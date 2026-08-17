"""NEIS HTTP 경계와 MCP 오류 변환 통합 테스트."""

import httpx
import pytest
import respx
from datetime import datetime
from zoneinfo import ZoneInfo
from mcp.shared.memory import create_connected_server_and_client_session
from mcp.types import TextContent

from bsl_mcp.client import NeisClient
from bsl_mcp.server import create_server
from bsl_mcp.settings import Settings


def _school_payload() -> dict[str, object]:
    return {
        "schoolInfo": [
            {"head": [{"RESULT": {"CODE": "INFO-000", "MESSAGE": "정상"}}]},
            {
                "row": [
                    {
                        "SD_SCHUL_CODE": "7010001",
                        "ATPT_OFCDC_SC_CODE": "B10",
                        "SCHUL_NM": "서울예시고등학교",
                        "ATPT_OFCDC_SC_NM": "서울특별시교육청",
                        "LCTN_SC_NM": "서울특별시",
                        "SCHUL_KND_SC_NM": "고등학교",
                    }
                ]
            },
        ]
    }


def _meal_payload(meal_ymd: str) -> dict[str, object]:
    return {
        "mealServiceDietInfo": [
            {"head": [{"RESULT": {"CODE": "INFO-000", "MESSAGE": "정상"}}]},
            {
                "row": [
                    {
                        "MMEAL_SC_CODE": "2",
                        "MLSV_YMD": meal_ymd,
                        "DDISH_NM": "현미밥<br/>된장찌개",
                        "ORPLC_INFO": "쌀: 국내산",
                        "NTR_INFO": "단백질(g): 25.3",
                        "CAL_INFO": "650 Kcal",
                        "MLSV_FGR": "450",
                    }
                ]
            },
        ]
    }


@pytest.mark.anyio
@respx.mock
async def test_neis_school_search_through_mcp() -> None:
    route = respx.get("https://neis.example/hub/schoolInfo").mock(
        return_value=httpx.Response(200, json=_school_payload())
    )
    settings = Settings(neis_api_key="secret", neis_base_url="https://neis.example")
    server = create_server(
        settings,
        NeisClient(
            base_url=settings.neis_base_url,
            api_key=settings.neis_api_key or "",
            timeout_seconds=settings.neis_timeout_seconds,
        ),
    )

    async with create_connected_server_and_client_session(
        server, raise_exceptions=False
    ) as session:
        result = await session.call_tool(
            "search_schools", {"school_name": "서울예시"}
        )

    assert route.called
    request = route.calls.last.request
    assert request.url.params["SCHUL_NM"] == "서울예시"
    assert request.url.params["KEY"] == "secret"
    assert result.isError is False
    assert result.structuredContent is not None
    assert result.structuredContent["schools"][0]["school_name"] == "서울예시고등학교"


@pytest.mark.anyio
@respx.mock
async def test_neis_lunch_query_uses_lunch_code() -> None:
    today = datetime.now(tz=ZoneInfo("Asia/Seoul")).date()
    respx.get("https://neis.example/hub/schoolInfo").mock(
        return_value=httpx.Response(200, json=_school_payload())
    )
    meal_route = respx.get(
        "https://neis.example/hub/mealServiceDietInfo"
    ).mock(
        return_value=httpx.Response(
            200, json=_meal_payload(today.strftime("%Y%m%d"))
        )
    )
    settings = Settings(neis_api_key="secret", neis_base_url="https://neis.example")
    server = create_server(
        settings,
        NeisClient(
            base_url=settings.neis_base_url,
            api_key=settings.neis_api_key or "",
            timeout_seconds=settings.neis_timeout_seconds,
        ),
    )

    async with create_connected_server_and_client_session(
        server, raise_exceptions=False
    ) as session:
        result = await session.call_tool(
            "get_school_lunches",
            {
                "education_office_code": "B10",
                "school_code": "7010001",
                "from_date": today.isoformat(),
                "to_date": today.isoformat(),
            },
        )

    request = meal_route.calls.last.request
    assert request.url.params["MMEAL_SC_CODE"] == "2"
    assert request.url.params["MLSV_FROM_YMD"] == today.strftime("%Y%m%d")
    assert result.isError is False
    assert result.structuredContent is not None
    assert result.structuredContent["meals"][0]["dishes"] == ["현미밥", "된장찌개"]


@pytest.mark.anyio
@respx.mock
async def test_empty_neis_meals_are_mcp_tool_error() -> None:
    today = datetime.now(tz=ZoneInfo("Asia/Seoul")).date()
    respx.get("https://neis.example/hub/schoolInfo").mock(
        return_value=httpx.Response(200, json=_school_payload())
    )
    respx.get("https://neis.example/hub/mealServiceDietInfo").mock(
        return_value=httpx.Response(
            200, json={"RESULT": {"CODE": "INFO-200", "MESSAGE": "데이터 없음"}}
        )
    )
    settings = Settings(neis_api_key="secret", neis_base_url="https://neis.example")
    server = create_server(
        settings,
        NeisClient(
            base_url=settings.neis_base_url,
            api_key=settings.neis_api_key or "",
            timeout_seconds=settings.neis_timeout_seconds,
        ),
    )

    async with create_connected_server_and_client_session(
        server, raise_exceptions=False
    ) as session:
        result = await session.call_tool(
            "get_school_lunches",
            {
                "education_office_code": "B10",
                "school_code": "7010001",
                "from_date": today.isoformat(),
                "to_date": today.isoformat(),
            },
        )

    assert result.isError is True
    assert isinstance(result.content[0], TextContent)
    assert result.content[0].text.endswith("선택한 기간에 중식 정보가 없습니다.")


@pytest.mark.anyio
@respx.mock
async def test_timeout_is_safe_mcp_tool_error() -> None:
    respx.get("https://neis.example/hub/schoolInfo").mock(
        side_effect=httpx.ReadTimeout("contains-secret-key")
    )
    settings = Settings(neis_api_key="secret", neis_base_url="https://neis.example")
    server = create_server(
        settings,
        NeisClient(
            base_url=settings.neis_base_url,
            api_key=settings.neis_api_key or "",
            timeout_seconds=settings.neis_timeout_seconds,
        ),
    )

    async with create_connected_server_and_client_session(
        server, raise_exceptions=False
    ) as session:
        result = await session.call_tool(
            "search_schools", {"school_name": "서울예시"}
        )

    assert result.isError is True
    assert isinstance(result.content[0], TextContent)
    assert result.content[0].text.endswith(
        "NEIS 응답이 지연되거나 연결할 수 없습니다."
    )
    assert "secret" not in result.content[0].text
