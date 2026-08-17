"""애플리케이션 설정. 환경 변수는 시작 시 검증한다."""

from functools import lru_cache

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """`NEIS_*`, `CORS_ALLOWED_ORIGINS`, `LOG_LEVEL` 환경 변수를 검증한다."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    neis_api_key: str | None = Field(
        default=None, description="NEIS 인증키(고정 fixture 모드에서는 불필요)"
    )
    neis_base_url: str = Field(
        default="https://open.neis.go.kr", description="NEIS API 호스트"
    )
    neis_timeout_seconds: float = Field(
        default=15.0, gt=0, description="외부 요청 전체 타임아웃(초)"
    )
    neis_fixture_mode: bool = Field(
        default=False,
        description=(
            "true면 실제 NEIS 호출 대신 결정적인 고정 데이터를 반환한다"
            "(E2E·데모 전용, TRD 12.5)"
        ),
    )
    cors_allowed_origins: str = Field(
        default="http://localhost:5173",
        description="쉼표로 구분된 허용 origin 목록",
    )
    log_level: str = Field(default="INFO", description="애플리케이션 로그 수준")

    @model_validator(mode="after")
    def _require_api_key_unless_fixture_mode(self) -> "Settings":
        if not self.neis_fixture_mode and not self.neis_api_key:
            raise ValueError(
                "NEIS_API_KEY is required unless NEIS_FIXTURE_MODE=true"
            )
        return self

    @property
    def cors_allowed_origin_list(self) -> list[str]:
        return [
            origin.strip()
            for origin in self.cors_allowed_origins.split(",")
            if origin.strip()
        ]


@lru_cache
def get_settings() -> Settings:
    """설정을 한 번만 로드하고 이후 요청에서 재사용한다."""

    return Settings()  # type: ignore[call-arg]

