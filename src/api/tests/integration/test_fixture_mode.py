"""고정 fixture 모드(`NEIS_FIXTURE_MODE=true`) 통합 테스트.

실제 NEIS API 키 없이도 `/schools`와 `/schools/{code}/meals`가 결정적인
데이터를 반환하는지 검증한다(TRD 12.5의 E2E 전략이 의존하는 동작).
"""

from __future__ import annotations

from collections.abc import Iterator
from datetime import timedelta

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from bsl_api.services.dates import today_kst

TODAY = today_kst()
FROM_ISO = (TODAY - timedelta(days=1)).isoformat()
TO_ISO = TODAY.isoformat()


@pytest.fixture
def fixture_mode_client(monkeypatch: pytest.MonkeyPatch) -> Iterator[TestClient]:
    """`NEIS_API_KEY` 없이 `NEIS_FIXTURE_MODE=true`로 앱을 구성한다."""

    monkeypatch.delenv("NEIS_API_KEY", raising=False)
    monkeypatch.setenv("NEIS_FIXTURE_MODE", "true")
    monkeypatch.setenv("CORS_ALLOWED_ORIGINS", "http://localhost:5173")

    from bsl_api.dependencies import get_neis_client
    from bsl_api.main import create_app
    from bsl_api.settings import get_settings

    get_settings.cache_clear()
    get_neis_client.cache_clear()
    app: FastAPI = create_app()
    with TestClient(app) as test_client:
        yield test_client
    get_settings.cache_clear()
    get_neis_client.cache_clear()


def test_fixture_mode_does_not_require_api_key(
    fixture_mode_client: TestClient,
) -> None:
    from bsl_api.settings import get_settings

    settings = get_settings()
    assert settings.neis_fixture_mode is True
    assert settings.neis_api_key is None


def test_fixture_mode_search_schools_returns_deterministic_result(
    fixture_mode_client: TestClient,
) -> None:
    response = fixture_mode_client.get(
        "/api/v1/schools", params={"name": "서울고정예시"}
    )

    assert response.status_code == 200
    body = response.json()
    assert body["total"] >= 1
    assert all("서울고정예시" in item["schoolName"] for item in body["items"])


def test_fixture_mode_search_schools_no_match_returns_empty(
    fixture_mode_client: TestClient,
) -> None:
    response = fixture_mode_client.get(
        "/api/v1/schools", params={"name": "존재하지않는학교이름"}
    )

    assert response.status_code == 200
    assert response.json() == {"items": [], "total": 0}


def test_fixture_mode_meals_include_populated_and_empty_days(
    fixture_mode_client: TestClient,
) -> None:
    search = fixture_mode_client.get(
        "/api/v1/schools", params={"name": "서울고정예시고등학교"}
    )
    school = search.json()["items"][0]

    response = fixture_mode_client.get(
        f"/api/v1/schools/{school['schoolCode']}/meals",
        params={
            "officeCode": school["educationOfficeCode"],
            "from": FROM_ISO,
            "to": TO_ISO,
        },
    )

    assert response.status_code == 200
    body = response.json()
    meal_dates = {meal["date"] for meal in body["meals"]}

    # 백엔드는 데이터가 있는 날짜만 반환하고(프론트가 "급식 정보 없음"으로
    # 빈 날짜를 채운다), 고정 클라이언트는 조회 범위의 마지막 날을
    # 의도적으로 비워 두어 빈 상태를 결정적으로 검증할 수 있게 한다.
    assert TO_ISO not in meal_dates
    assert any(meal["dishes"] for meal in body["meals"])
