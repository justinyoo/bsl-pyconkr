"""Streamable HTTP MCP 서버 진입점."""

from bsl_mcp.server import create_server
from bsl_mcp.settings import get_settings


def main() -> None:
    server = create_server(get_settings())
    server.run(transport="streamable-http")


if __name__ == "__main__":
    main()
