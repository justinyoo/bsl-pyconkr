"""표준 오류 응답(`ProblemDetail`)과 애플리케이션 예외를 정의한다."""

from __future__ import annotations

from typing import Any

from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel

_PROBLEM_BASE_URI = "https://example.invalid/problems"


class ProblemDetail(BaseModel):
    """RFC 9457 스타일 오류 Payload."""

    type: str
    title: str
    status: int
    detail: str
    instance: str | None = None
    code: str
    errors: dict[str, list[str]] | None = None


class ApiError(Exception):
    """API 계약에 정의된 오류 코드를 나타내는 기본 예외."""

    def __init__(
        self,
        *,
        status_code: int,
        code: str,
        title: str,
        detail: str,
        errors: dict[str, list[str]] | None = None,
    ) -> None:
        super().__init__(detail)
        self.status_code = status_code
        self.code = code
        self.title = title
        self.detail = detail
        self.errors = errors


class InvalidRequestError(ApiError):
    def __init__(
        self, detail: str, errors: dict[str, list[str]] | None = None
    ) -> None:
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            code="INVALID_REQUEST",
            title="Invalid request",
            detail=detail,
            errors=errors,
        )


class InvalidDateRangeError(ApiError):
    def __init__(
        self, detail: str, errors: dict[str, list[str]] | None = None
    ) -> None:
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            code="INVALID_DATE_RANGE",
            title="Invalid date range",
            detail=detail,
            errors=errors,
        )


class SchoolNotFoundError(ApiError):
    def __init__(self, detail: str = "요청한 학교를 확인할 수 없습니다.") -> None:
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            code="SCHOOL_NOT_FOUND",
            title="School not found",
            detail=detail,
        )


class RateLimitedError(ApiError):
    def __init__(self, detail: str = "요청이 너무 많습니다. 잠시 후 다시 시도해 주세요.") -> None:
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            code="RATE_LIMITED",
            title="Rate limited",
            detail=detail,
        )


class UpstreamError(ApiError):
    def __init__(self, detail: str = "NEIS 응답을 처리할 수 없습니다.") -> None:
        super().__init__(
            status_code=status.HTTP_502_BAD_GATEWAY,
            code="UPSTREAM_ERROR",
            title="Upstream error",
            detail=detail,
        )


class UpstreamUnavailableError(ApiError):
    def __init__(
        self, detail: str = "NEIS에 연결할 수 없습니다. 잠시 후 다시 시도해 주세요."
    ) -> None:
        super().__init__(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            code="UPSTREAM_UNAVAILABLE",
            title="Upstream unavailable",
            detail=detail,
        )


def _problem_response(
    request: Request,
    *,
    status_code: int,
    code: str,
    title: str,
    detail: str,
    errors: dict[str, list[str]] | None = None,
) -> JSONResponse:
    problem = ProblemDetail(
        type=f"{_PROBLEM_BASE_URI}/{code.lower().replace('_', '-')}",
        title=title,
        status=status_code,
        detail=detail,
        instance=str(request.url.path),
        code=code,
        errors=errors,
    )
    return JSONResponse(
        status_code=status_code,
        content=problem.model_dump(exclude_none=True),
        media_type="application/problem+json",
    )


async def api_error_handler(request: Request, exc: ApiError) -> JSONResponse:
    return _problem_response(
        request,
        status_code=exc.status_code,
        code=exc.code,
        title=exc.title,
        detail=exc.detail,
        errors=exc.errors,
    )


def _flatten_validation_errors(
    exc: RequestValidationError,
) -> dict[str, list[str]]:
    flattened: dict[str, list[str]] = {}
    for error in exc.errors():
        location = ".".join(str(part) for part in error["loc"][1:]) or "request"
        flattened.setdefault(location, []).append(error["msg"])
    return flattened


async def validation_error_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    return _problem_response(
        request,
        status_code=status.HTTP_400_BAD_REQUEST,
        code="INVALID_REQUEST",
        title="Invalid request",
        detail="요청 파라미터가 올바르지 않습니다.",
        errors=_flatten_validation_errors(exc),
    )


async def unhandled_exception_handler(
    request: Request, exc: Exception
) -> JSONResponse:
    return _problem_response(
        request,
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        code="INTERNAL_ERROR",
        title="Internal error",
        detail="예상하지 못한 오류가 발생했습니다.",
    )


def register_exception_handlers(app: Any) -> None:
    app.add_exception_handler(ApiError, api_error_handler)
    app.add_exception_handler(RequestValidationError, validation_error_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)
