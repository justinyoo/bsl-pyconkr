"""`GET /api/v1/schools` 통합 테스트.

`respx`로 HTTPX의 NEIS 호출만 대체하고 FastAPI 라우팅과 Pydantic 검증은
실제로 실행한다.
"""

from __future__ import annotations

import httpx
import respx
from fastapi.testclient import TestClient

NEIS_BASE_URL = "https://neis.invalid"


@respx.mock
def test_search_schools_normalizes_neis_response(client: TestClient) -> None:
    respx.get(f"{NEIS_BASE_URL}/hub/schoolInfo").mock(
        return_value=httpx.Response(
            200,
            json={
                "schoolInfo": [
                    {"head": [{"list_total_count": 1}]},
                    {
                        "row": [
                            {
                                "ATPT_OFCDC_SC_CODE": "B10",
                                "ATPT_OFCDC_SC_NM": "서울특별시교육청",
                                "SD_SCHUL_CODE": "7010113",
                                "SCHUL_NM": "서울고등학교",
                                "LCTN_SC_NM": "서울특별시",
                                "SCHUL_KND_SC_NM": "고등학교",
                            }
                        ]
                    },
                ]
            },
        )
    )

    response = client.get("/api/v1/schools", params={"name": "서울고"})

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert body["items"][0] == {
        "schoolCode": "7010113",
        "educationOfficeCode": "B10",
        "schoolName": "서울고등학교",
        "educationOfficeName": "서울특별시교육청",
        "locationName": "서울특별시",
        "schoolType": "고등학교",
    }


@respx.mock
def test_search_schools_returns_empty_items_for_info_200(client: TestClient) -> None:
    respx.get(f"{NEIS_BASE_URL}/hub/schoolInfo").mock(
        return_value=httpx.Response(
            200,
            json={"RESULT": {"CODE": "INFO-200", "MESSAGE": "해당하는 데이터가 없습니다."}},
        )
    )

    response = client.get("/api/v1/schools", params={"name": "존재하지않는학교"})

    assert response.status_code == 200
    assert response.json() == {"items": [], "total": 0}


def test_search_schools_rejects_short_query(client: TestClient) -> None:
    response = client.get("/api/v1/schools", params={"name": "가"})

    assert response.status_code == 400
    assert response.headers["content-type"].startswith("application/problem+json")
    body = response.json()
    assert body["code"] == "INVALID_REQUEST"


def test_search_schools_rejects_missing_query(client: TestClient) -> None:
    response = client.get("/api/v1/schools")

    assert response.status_code == 400
    body = response.json()
    assert body["code"] == "INVALID_REQUEST"


@respx.mock
def test_search_schools_maps_neis_rate_limit_to_429(client: TestClient) -> None:
    respx.get(f"{NEIS_BASE_URL}/hub/schoolInfo").mock(
        return_value=httpx.Response(
            200, json={"RESULT": {"CODE": "ERROR-337", "MESSAGE": "일별 트래픽 초과"}}
        )
    )

    response = client.get("/api/v1/schools", params={"name": "서울고"})

    assert response.status_code == 429
    assert response.json()["code"] == "RATE_LIMITED"


@respx.mock
def test_search_schools_maps_neis_timeout_to_503(client: TestClient) -> None:
    respx.get(f"{NEIS_BASE_URL}/hub/schoolInfo").mock(
        side_effect=httpx.TimeoutException("timed out")
    )

    response = client.get("/api/v1/schools", params={"name": "서울고"})

    assert response.status_code == 503
    assert response.json()["code"] == "UPSTREAM_UNAVAILABLE"


@respx.mock
def test_search_schools_does_not_leak_api_key(client: TestClient) -> None:
    route = respx.get(f"{NEIS_BASE_URL}/hub/schoolInfo").mock(
        return_value=httpx.Response(
            200,
            json={
                "schoolInfo": [
                    {"head": [{"list_total_count": 0}]},
                    {"row": []},
                ]
            },
        )
    )

    response = client.get("/api/v1/schools", params={"name": "서울고"})

    assert "test-key" not in response.text
    assert route.calls.last.request.url.params["KEY"] == "test-key"
