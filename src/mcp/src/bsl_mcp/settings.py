"""환경 변수 기반 MCP 서버 설정."""

from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

LogLevel = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]


class Settings(BaseSettings):
    """시작 시 NEIS 및 MCP 전송 설정을 검증한다."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    neis_api_key: str | None = None
    neis_base_url: str = "https://open.neis.go.kr"
    neis_timeout_seconds: float = Field(default=15.0, gt=0)
    neis_fixture_mode: bool = False
    mcp_host: str = "0.0.0.0"
    mcp_port: int = Field(default=8001, ge=1, le=65535)
    log_level: LogLevel = "INFO"

    @field_validator("log_level", mode="before")
    @classmethod
    def normalize_log_level(cls, value: object) -> object:
        return value.upper() if isinstance(value, str) else value

    @model_validator(mode="after")
    def require_api_key(self) -> "Settings":
        if not self.neis_fixture_mode and not self.neis_api_key:
            raise ValueError(
                "NEIS_API_KEY is required unless NEIS_FIXTURE_MODE=true"
            )
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
