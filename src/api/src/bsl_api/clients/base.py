"""NEIS 클라이언트 공용 인터페이스.

서비스 계층은 이 Protocol에만 의존하고, 실제 HTTP 클라이언트(`NeisClient`)와
E2E용 고정 데이터 클라이언트(`FixtureNeisClient`)는 이를 만족하는 구현체다.
"""

from __future__ import annotations

from typing import Any, Protocol


class SchoolAndMealClient(Protocol):
    """학교 검색·조회, 급식 조회에 필요한 최소 인터페이스."""

    async def search_schools(self, name: str) -> list[dict[str, Any]]: ...

    async def get_school(
        self, *, office_code: str, school_code: str
    ) -> list[dict[str, Any]]: ...

    async def get_lunches(
        self,
        *,
        office_code: str,
        school_code: str,
        from_ymd: str,
        to_ymd: str,
    ) -> list[dict[str, Any]]: ...
