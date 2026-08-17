"""NEIS 결과 코드별 예외 매핑 단위 테스트. 네트워크를 사용하지 않는다."""

from __future__ import annotations

import pytest

from bsl_api.clients.exceptions import (
    NeisAuthenticationError,
    NeisRateLimitedError,
    NeisUpstreamError,
)
from bsl_api.clients.neis_client import NeisClient


@pytest.fixture
def client() -> NeisClient:
    return NeisClient(
        base_url="https://neis.invalid", api_key="test-key", timeout_seconds=5
    )


def test_extract_rows_returns_empty_list_for_info_200(client: NeisClient) -> None:
    payload = {"RESULT": {"CODE": "INFO-200", "MESSAGE": "해당하는 데이터가 없습니다."}}
    assert client._extract_rows(payload, "schoolInfo") == []


def test_extract_rows_returns_empty_list_for_bare_code_200(
    client: NeisClient,
) -> None:
    payload = {"RESULT": {"CODE": "200", "MESSAGE": "no data"}}
    assert client._extract_rows(payload, "schoolInfo") == []


@pytest.mark.parametrize("code", ["337", "336"])
def test_extract_rows_raises_rate_limited(client: NeisClient, code: str) -> None:
    payload = {"RESULT": {"CODE": code, "MESSAGE": "traffic limit"}}
    with pytest.raises(NeisRateLimitedError):
        client._extract_rows(payload, "schoolInfo")


@pytest.mark.parametrize("code", ["100", "290", "300"])
def test_extract_rows_raises_authentication_error(
    client: NeisClient, code: str
) -> None:
    payload = {"RESULT": {"CODE": code, "MESSAGE": "auth error"}}
    with pytest.raises(NeisAuthenticationError):
        client._extract_rows(payload, "schoolInfo")


@pytest.mark.parametrize("code", ["310", "333", "500", "600", "601"])
def test_extract_rows_raises_upstream_error_for_other_codes(
    client: NeisClient, code: str
) -> None:
    payload = {"RESULT": {"CODE": code, "MESSAGE": "server error"}}
    with pytest.raises(NeisUpstreamError):
        client._extract_rows(payload, "schoolInfo")


def test_extract_rows_parses_head_and_row_sections(client: NeisClient) -> None:
    payload = {
        "schoolInfo": [
            {"head": [{"list_total_count": 1}, {"RESULT": {"CODE": "INFO-000", "MESSAGE": "ok"}}]},
            {"row": [{"SCHUL_NM": "서울고등학교"}]},
        ]
    }
    rows = client._extract_rows(payload, "schoolInfo")
    assert rows == [{"SCHUL_NM": "서울고등학교"}]


def test_extract_rows_raises_for_unexpected_structure(client: NeisClient) -> None:
    payload = {"unexpected": "shape"}
    with pytest.raises(NeisUpstreamError):
        client._extract_rows(payload, "schoolInfo")
