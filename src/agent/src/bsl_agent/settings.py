"""에이전트 앱 환경 변수 설정."""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    agent_host: str = "0.0.0.0"
    agent_port: int = Field(default=8002, ge=1, le=65535)
    agent_devui_port: int = Field(default=8080, ge=1, le=65535)
    agent_fixture_mode: bool = False
    copilot_model: str | None = None
    mcp_server_url: str = "http://localhost:8001/mcp"
    cors_allowed_origins: str = "http://localhost:5173"

    @property
    def allowed_origins(self) -> list[str]:
        return [
            origin.strip()
            for origin in self.cors_allowed_origins.split(",")
            if origin.strip()
        ]


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
