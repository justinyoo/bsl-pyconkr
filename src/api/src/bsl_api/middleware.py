"""요청 상관관계 ID와 완료 로그를 제공하는 HTTP 미들웨어."""

from __future__ import annotations

import logging
import re
from time import perf_counter
from uuid import uuid4

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

REQUEST_ID_HEADER = "X-Request-ID"
_REQUEST_ID_PATTERN = re.compile(r"^[A-Za-z0-9._-]{1,128}$")
_LOGGER = logging.getLogger("bsl_api.requests")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """각 요청에 안전한 ID를 부여하고 완료 상태를 한 줄로 기록한다."""

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        request_id = self._request_id(request)
        started_at = perf_counter()

        try:
            response = await call_next(request)
        except Exception:
            _LOGGER.exception(
                "request failed request_id=%s method=%s path=%s",
                request_id,
                request.method,
                request.url.path,
            )
            raise

        duration_ms = (perf_counter() - started_at) * 1000
        response.headers[REQUEST_ID_HEADER] = request_id
        _LOGGER.info(
            "request completed request_id=%s method=%s path=%s status=%d "
            "duration_ms=%.2f",
            request_id,
            request.method,
            request.url.path,
            response.status_code,
            duration_ms,
        )
        return response

    @staticmethod
    def _request_id(request: Request) -> str:
        supplied = request.headers.get(REQUEST_ID_HEADER)
        if supplied and _REQUEST_ID_PATTERN.fullmatch(supplied):
            return supplied
        return str(uuid4())
