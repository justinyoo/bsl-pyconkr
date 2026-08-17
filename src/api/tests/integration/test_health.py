"""`GET /api/v1/health` 통합 테스트."""

from __future__ import annotations

import logging
from uuid import UUID

import pytest
from fastapi.testclient import TestClient


def test_health_returns_ok(client: TestClient) -> None:
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_health_returns_and_logs_request_id(
    client: TestClient, caplog: pytest.LogCaptureFixture
) -> None:
    request_id = "health-check-123"

    with caplog.at_level(logging.INFO, logger="bsl_api.requests"):
        response = client.get(
            "/api/v1/health", headers={"X-Request-ID": request_id}
        )

    assert response.headers["X-Request-ID"] == request_id
    assert f"request_id={request_id}" in caplog.text


def test_health_replaces_invalid_request_id(client: TestClient) -> None:
    response = client.get(
        "/api/v1/health", headers={"X-Request-ID": "invalid request id\n"}
    )

    assert UUID(response.headers["X-Request-ID"])
