"""공식 MCP Python SDK 1.x 기반 도구 서버."""

from datetime import date
from typing import Annotated, Awaitable, Callable, TypeVar

from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.exceptions import ToolError
from pydantic import Field

from bsl_mcp.client import FixtureNeisClient, NeisClient, SchoolAndMealClient
from bsl_mcp.exceptions import (
    MealsNotFoundError,
    NeisAuthenticationError,
    NeisRateLimitedError,
    NeisResponseError,
    NeisUnavailableError,
    SchoolNotFoundError,
)
from bsl_mcp.models import SchoolMealsResult, SchoolSearchResult
from bsl_mcp.service import get_school_lunches, list_random_schools, search_schools
from bsl_mcp.settings import Settings

T = TypeVar("T")


async def _as_tool_error(operation: Callable[[], Awaitable[T]]) -> T:
    try:
        return await operation()
    except ValueError as exc:
        raise ToolError(str(exc)) from exc
    except SchoolNotFoundError as exc:
        raise ToolError("조건과 일치하는 학교를 찾을 수 없습니다.") from exc
    except MealsNotFoundError as exc:
        raise ToolError("선택한 기간에 중식 정보가 없습니다.") from exc
    except NeisAuthenticationError as exc:
        raise ToolError("NEIS 인증에 실패했습니다. 서버 설정을 확인해 주세요.") from exc
    except NeisRateLimitedError as exc:
        raise ToolError("NEIS 요청 한도를 초과했습니다. 잠시 후 다시 시도해 주세요.") from exc
    except NeisUnavailableError as exc:
        raise ToolError("NEIS 응답이 지연되거나 연결할 수 없습니다.") from exc
    except NeisResponseError as exc:
        raise ToolError("NEIS가 처리할 수 없는 응답을 반환했습니다.") from exc


def _client_from_settings(settings: Settings) -> SchoolAndMealClient:
    if settings.neis_fixture_mode:
        return FixtureNeisClient()
    return NeisClient(
        base_url=settings.neis_base_url,
        api_key=settings.neis_api_key or "",
        timeout_seconds=settings.neis_timeout_seconds,
    )


def create_server(
    settings: Settings, client: SchoolAndMealClient | None = None
) -> FastMCP:
    """설정과 교체 가능한 NEIS 클라이언트로 MCP 서버를 구성한다."""

    neis_client = client or _client_from_settings(settings)
    server = FastMCP(
        name="급식 배틀 MCP",
        instructions=(
            "학교 이름으로 후보를 찾은 뒤 교육청 코드와 학교 코드를 사용해 "
            "지정한 기간의 중식 정보를 조회합니다."
        ),
        host=settings.mcp_host,
        port=settings.mcp_port,
        streamable_http_path="/mcp",
        json_response=True,
        log_level=settings.log_level,
    )

    @server.tool(
        name="list_random_schools",
        title="무작위 학교 후보 조회",
        description=(
            "급식 비교 화면에서 선택할 무작위 학교 후보를 최대 10개 반환합니다."
        ),
    )
    async def list_random_schools_tool(
        count: Annotated[
            int, Field(default=10, ge=2, le=10, description="반환할 학교 후보 수")
        ] = 10,
    ) -> SchoolSearchResult:
        return await _as_tool_error(
            lambda: list_random_schools(neis_client, count=count)
        )

    @server.tool(
        name="search_schools",
        title="학교 검색",
        description=(
            "학교 이름 일부로 후보 학교의 이름, 교육청, 지역 및 식별 코드를 "
            "조회합니다."
        ),
    )
    async def search_school_tool(
        school_name: Annotated[
            str, Field(description="검색할 학교 이름의 일부(공백 제외 2자 이상)")
        ],
    ) -> SchoolSearchResult:
        return await _as_tool_error(
            lambda: search_schools(neis_client, school_name)
        )

    @server.tool(
        name="get_school_lunches",
        title="학교 중식 조회",
        description=(
            "교육청 코드와 학교 코드로 선택한 학교의 날짜별 중식 메뉴, 원산지, "
            "영양 정보, 칼로리 및 급식 인원을 조회합니다."
        ),
    )
    async def get_school_lunches_tool(
        education_office_code: Annotated[
            str, Field(description="학교 검색 결과의 교육청 코드")
        ],
        school_code: Annotated[str, Field(description="학교 행정표준코드")],
        from_date: Annotated[date, Field(description="조회 시작일(YYYY-MM-DD)")],
        to_date: Annotated[date, Field(description="조회 종료일(YYYY-MM-DD)")],
    ) -> SchoolMealsResult:
        return await _as_tool_error(
            lambda: get_school_lunches(
                neis_client,
                education_office_code=education_office_code,
                school_code=school_code,
                from_date=from_date,
                to_date=to_date,
            )
        )

    return server
