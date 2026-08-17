"""MCP 테스트 공통 fixture."""

from collections.abc import AsyncGenerator

import pytest
from mcp.client.session import ClientSession
from mcp.shared.memory import create_connected_server_and_client_session

from bsl_mcp.client import FixtureNeisClient
from bsl_mcp.server import create_server
from bsl_mcp.settings import Settings


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


@pytest.fixture
async def client_session() -> AsyncGenerator[ClientSession]:
    settings = Settings(neis_fixture_mode=True)
    server = create_server(settings, FixtureNeisClient())
    async with create_connected_server_and_client_session(
        server, raise_exceptions=False
    ) as session:
        yield session
