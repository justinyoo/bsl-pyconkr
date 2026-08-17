"""MCP 서버 내부에서 사용하는 NEIS 및 조회 예외."""


class NeisError(Exception):
    """NEIS 연동 오류의 기본 클래스."""


class NeisAuthenticationError(NeisError):
    """NEIS 인증 실패."""


class NeisRateLimitedError(NeisError):
    """NEIS 요청 제한 초과."""


class NeisUnavailableError(NeisError):
    """NEIS 연결 실패 또는 시간 초과."""


class NeisResponseError(NeisError):
    """NEIS 오류 응답 또는 잘못된 응답 구조."""


class SchoolNotFoundError(Exception):
    """학교 식별 정보와 일치하는 학교가 없음."""


class MealsNotFoundError(Exception):
    """조회 기간에 중식 정보가 없음."""
