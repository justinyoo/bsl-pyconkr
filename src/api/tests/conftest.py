"""공통 pytest fixture: 테스트 환경 변수와 앱/클라이언트 팩토리."""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient


@pytest.fixture(autouse=True)
def test_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """NEIS_API_KEY 등 필수 환경 변수를 테스트용 값으로 고정한다.

    실제 NEIS API 키 없이도 전체 테스트가 통과해야 한다.
    """

    monkeypatch.setenv("NEIS_API_KEY", "test-key")
    monkeypatch.setenv("NEIS_BASE_URL", "https://neis.invalid")
    monkeypatch.setenv("NEIS_TIMEOUT_SECONDS", "5")
    monkeypatch.setenv("CORS_ALLOWED_ORIGINS", "http://localhost:5173")
    monkeypatch.delenv("LOG_LEVEL", raising=False)


@pytest.fixture
def app(test_env: None) -> Iterator[FastAPI]:
    from bsl_api.dependencies import get_neis_client
    from bsl_api.main import create_app
    from bsl_api.settings import get_settings

    get_settings.cache_clear()
    get_neis_client.cache_clear()
    created_app = create_app()
    yield created_app
    get_settings.cache_clear()
    get_neis_client.cache_clear()


@pytest.fixture
def client(app: FastAPI) -> Iterator[TestClient]:
    with TestClient(app) as test_client:
        yield test_client

