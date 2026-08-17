"""`GET /api/v1/schools/{schoolCode}/meals` 통합 테스트."""

from __future__ import annotations

import httpx
import respx
from fastapi.testclient import TestClient

from bsl_api.services.dates import today_kst

NEIS_BASE_URL = "https://neis.invalid"

# 테스트 실행 시점의 실제 "오늘"을 기준으로 유효한 범위를 계산해, 날짜가
# 하드코딩된 값이 시간이 지나 허용 범위를 벗어나 테스트가 깨지는 것을 막는다.
TODAY = today_kst()
FROM_DATE = TODAY.replace(day=1)
TO_DATE = TODAY
FROM_ISO = FROM_DATE.isoformat()
TO_ISO = TO_DATE.isoformat()
FROM_YMD = FROM_DATE.strftime("%Y%m%d")
TO_YMD = TO_DATE.strftime("%Y%m%d")

SCHOOL_ROW = {
    "ATPT_OFCDC_SC_CODE": "B10",
    "ATPT_OFCDC_SC_NM": "서울특별시교육청",
    "SD_SCHUL_CODE": "7010113",
    "SCHUL_NM": "서울고등학교",
    "LCTN_SC_NM": "서울특별시",
    "SCHUL_KND_SC_NM": "고등학교",
}


def _mock_school_lookup(rows: list[dict] | None = None) -> None:
    school_rows = SCHOOL_ROW if rows is None else rows
    if rows is None:
        payload = {"schoolInfo": [{"head": [{"list_total_count": 1}]}, {"row": [school_rows]}]}
    else:
        payload = {"schoolInfo": [{"head": [{"list_total_count": len(rows)}]}, {"row": rows}]}
    respx.get(f"{NEIS_BASE_URL}/hub/schoolInfo").mock(
        return_value=httpx.Response(200, json=payload)
    )


@respx.mock
def test_get_meals_returns_normalized_lunch_list(client: TestClient) -> None:
    _mock_school_lookup()
    respx.get(f"{NEIS_BASE_URL}/hub/mealServiceDietInfo").mock(
        return_value=httpx.Response(
            200,
            json={
                "mealServiceDietInfo": [
                    {"head": [{"list_total_count": 1}]},
                    {
                        "row": [
                            {
                                "ATPT_OFCDC_SC_CODE": "B10",
                                "ATPT_OFCDC_SC_NM": "서울특별시교육청",
                                "SD_SCHUL_CODE": "7010113",
                                "SCHUL_NM": "서울고등학교",
                                "MMEAL_SC_CODE": "2",
                                "MMEAL_SC_NM": "중식",
                                "MLSV_YMD": TO_YMD,
                                "DDISH_NM": "현미밥<br/>미역국",
                                "ORPLC_INFO": "쌀: 국내산",
                                "CAL_INFO": "742.3 Kcal",
                                "NTR_INFO": "탄수화물(g): 92.1",
                                "MLSV_FGR": 530.0,
                            }
                        ]
                    },
                ]
            },
        )
    )

    response = client.get(
        "/api/v1/schools/7010113/meals",
        params={"officeCode": "B10", "from": FROM_ISO, "to": TO_ISO},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["school"] == {
        "schoolCode": "7010113",
        "educationOfficeCode": "B10",
        "schoolName": "서울고등학교",
        "educationOfficeName": "서울특별시교육청",
    }
    assert body["from"] == FROM_ISO
    assert body["to"] == TO_ISO
    assert len(body["meals"]) == 1
    meal = body["meals"][0]
    assert meal["date"] == TO_ISO
    assert meal["mealType"] == "lunch"
    assert meal["dishes"] == ["현미밥", "미역국"]
    assert meal["servingCount"] == 530


@respx.mock
def test_get_meals_returns_empty_meals_for_info_200(client: TestClient) -> None:
    _mock_school_lookup()
    respx.get(f"{NEIS_BASE_URL}/hub/mealServiceDietInfo").mock(
        return_value=httpx.Response(
            200,
            json={"RESULT": {"CODE": "INFO-200", "MESSAGE": "해당하는 데이터가 없습니다."}},
        )
    )

    response = client.get(
        "/api/v1/schools/7010113/meals",
        params={"officeCode": "B10", "from": FROM_ISO, "to": TO_ISO},
    )

    assert response.status_code == 200
    assert response.json()["meals"] == []


@respx.mock
def test_get_meals_returns_meals_sorted_ascending(client: TestClient) -> None:
    _mock_school_lookup()

    def _row(day: str) -> dict:
        return {
            "ATPT_OFCDC_SC_CODE": "B10",
            "ATPT_OFCDC_SC_NM": "서울특별시교육청",
            "SD_SCHUL_CODE": "7010113",
            "SCHUL_NM": "서울고등학교",
            "MMEAL_SC_CODE": "2",
            "MMEAL_SC_NM": "중식",
            "MLSV_YMD": day,
            "DDISH_NM": "메뉴",
        }

    respx.get(f"{NEIS_BASE_URL}/hub/mealServiceDietInfo").mock(
        return_value=httpx.Response(
            200,
            json={
                "mealServiceDietInfo": [
                    {"head": [{"list_total_count": 2}]},
                    {"row": [_row(TO_YMD), _row(FROM_YMD)]},
                ]
            },
        )
    )

    response = client.get(
        "/api/v1/schools/7010113/meals",
        params={"officeCode": "B10", "from": FROM_ISO, "to": TO_ISO},
    )

    dates = [meal["date"] for meal in response.json()["meals"]]
    assert dates == [FROM_ISO, TO_ISO]


@respx.mock
def test_get_meals_returns_404_when_school_missing(client: TestClient) -> None:
    respx.get(f"{NEIS_BASE_URL}/hub/schoolInfo").mock(
        return_value=httpx.Response(
            200,
            json={"RESULT": {"CODE": "INFO-200", "MESSAGE": "해당하는 데이터가 없습니다."}},
        )
    )

    response = client.get(
        "/api/v1/schools/0000000/meals",
        params={"officeCode": "B10", "from": FROM_ISO, "to": TO_ISO},
    )

    assert response.status_code == 404
    assert response.json()["code"] == "SCHOOL_NOT_FOUND"


def test_get_meals_rejects_reversed_date_range(client: TestClient) -> None:
    response = client.get(
        "/api/v1/schools/7010113/meals",
        params={"officeCode": "B10", "from": TO_ISO, "to": FROM_ISO},
    )

    assert response.status_code == 400
    assert response.json()["code"] == "INVALID_DATE_RANGE"


def test_get_meals_rejects_date_before_allowed_start(client: TestClient) -> None:
    response = client.get(
        "/api/v1/schools/7010113/meals",
        params={"officeCode": "B10", "from": "2000-01-01", "to": "2000-01-02"},
    )

    assert response.status_code == 400
    assert response.json()["code"] == "INVALID_DATE_RANGE"


def test_get_meals_rejects_invalid_date_format(client: TestClient) -> None:
    response = client.get(
        "/api/v1/schools/7010113/meals",
        params={"officeCode": "B10", "from": "not-a-date", "to": TO_ISO},
    )

    assert response.status_code == 400
    assert response.json()["code"] == "INVALID_REQUEST"


@respx.mock
def test_get_meals_maps_neis_server_error_to_502(client: TestClient) -> None:
    respx.get(f"{NEIS_BASE_URL}/hub/schoolInfo").mock(
        return_value=httpx.Response(
            200, json={"RESULT": {"CODE": "ERROR-500", "MESSAGE": "server error"}}
        )
    )

    response = client.get(
        "/api/v1/schools/7010113/meals",
        params={"officeCode": "B10", "from": FROM_ISO, "to": TO_ISO},
    )

    assert response.status_code == 502
    assert response.json()["code"] == "UPSTREAM_ERROR"
