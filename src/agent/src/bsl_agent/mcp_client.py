"""기존 급식 MCP 서버를 호출하는 결정론적 데이터 게이트웨이."""

from __future__ import annotations

from contextlib import asynccontextmanager
from datetime import date
from typing import AsyncIterator, Protocol

from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client
from mcp.types import CallToolResult

from bsl_agent.models import School, SchoolMealsResult, SchoolSearchResult


class MealGateway(Protocol):
    async def list_random_schools(self, count: int = 10) -> SchoolSearchResult: ...

    async def search_schools(self, school_name: str) -> SchoolSearchResult: ...

    async def get_school_lunch(
        self, school: School, meal_date: date
    ) -> SchoolMealsResult: ...


class McpToolError(RuntimeError):
    """MCP 도구가 안전한 오류 결과를 반환했을 때의 애플리케이션 예외."""


class MealNotFoundError(McpToolError):
    """선택한 날짜에 해당 학교의 중식 데이터가 없을 때의 예외."""


class McpMealGateway:
    def __init__(self, url: str) -> None:
        self._url = url

    @asynccontextmanager
    async def _session(self) -> AsyncIterator[ClientSession]:
        async with streamable_http_client(self._url) as (
            read_stream,
            write_stream,
            _,
        ):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                yield session

    @staticmethod
    def _structured(result: CallToolResult) -> dict[str, object]:
        if result.isError:
            message = "MCP 도구 호출에 실패했습니다."
            if result.content:
                text = getattr(result.content[0], "text", None)
                if isinstance(text, str) and text.strip():
                    message = text.strip()
            raise McpToolError(message)
        if result.structuredContent is None:
            raise McpToolError("MCP 도구가 구조화된 결과를 반환하지 않았습니다.")
        return result.structuredContent

    async def list_random_schools(self, count: int = 10) -> SchoolSearchResult:
        async with self._session() as session:
            result = await session.call_tool("list_random_schools", {"count": count})
        return SchoolSearchResult.model_validate(self._structured(result))

    async def search_schools(self, school_name: str) -> SchoolSearchResult:
        async with self._session() as session:
            result = await session.call_tool(
                "search_schools", {"school_name": school_name}
            )
        return SchoolSearchResult.model_validate(self._structured(result))

    async def get_school_lunch(
        self, school: School, meal_date: date
    ) -> SchoolMealsResult:
        async with self._session() as session:
            result = await session.call_tool(
                "get_school_lunches",
                {
                    "education_office_code": school.education_office_code,
                    "school_code": school.school_code,
                    "from_date": meal_date.isoformat(),
                    "to_date": meal_date.isoformat(),
                },
            )
        try:
            structured = self._structured(result)
        except McpToolError as exc:
            if "중식 정보가 없습니다." in str(exc):
                raise MealNotFoundError(str(exc)) from exc
            raise
        parsed = SchoolMealsResult.model_validate(structured)
        if len(parsed.meals) != 1 or parsed.meals[0].date != meal_date:
            raise McpToolError("선택한 날짜의 중식 정보가 정확히 한 건이어야 합니다.")
        return parsed
