"""NEIS 클라이언트 전용 예외.

라우터/서비스 계층은 이 예외를 `bsl_api.errors.ApiError` 계열로 변환한다.
"""

from __future__ import annotations


class NeisClientError(Exception):
    """NEIS 호출 중 발생한 오류의 기본 클래스."""


class NeisAuthenticationError(NeisClientError):
    """인증키가 유효하지 않거나 서비스 권한이 없는 경우."""


class NeisRateLimitedError(NeisClientError):
    """NEIS가 요청 제한을 반환한 경우."""


class NeisUpstreamError(NeisClientError):
    """NEIS가 처리 불가능한 오류를 반환한 경우."""


class NeisUnavailableError(NeisClientError):
    """NEIS 연결 실패 또는 타임아웃."""
