"""FastAPI 의존성 주입 헬퍼."""

from __future__ import annotations

from functools import lru_cache

from bsl_api.clients.base import SchoolAndMealClient
from bsl_api.clients.fixture_client import FixtureNeisClient
from bsl_api.clients.neis_client import NeisClient
from bsl_api.settings import get_settings

__all__ = ["SchoolAndMealClient", "get_neis_client"]


@lru_cache
def get_neis_client() -> SchoolAndMealClient:
    """설정을 기반으로 NEIS 클라이언트를 생성한다(요청 간 재사용).

    `NEIS_FIXTURE_MODE=true`이면 실제 NEIS 대신 결정적인 고정 데이터를
    반환하는 클라이언트를 사용한다(E2E·데모 전용, TRD 12.5).
    """

    settings = get_settings()
    if settings.neis_fixture_mode:
        return FixtureNeisClient()
    assert settings.neis_api_key is not None  # 설정 검증에서 보장됨
    return NeisClient(
        base_url=settings.neis_base_url,
        api_key=settings.neis_api_key,
        timeout_seconds=settings.neis_timeout_seconds,
    )

