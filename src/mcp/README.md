# 급식 배틀 MCP 서버

공식 MCP Python SDK 1.x의 Streamable HTTP 전송으로 NEIS 학교 검색과 중식 조회
도구를 제공합니다.

```sh
cd src/mcp
uv sync --locked
NEIS_API_KEY=... uv run bsl-mcp
```

fixture 모드에서는 실제 인증키나 NEIS 네트워크가 필요하지 않습니다.
`가온예시고등학교`는 급식 정보가 없는 부분 분석 흐름을 확인하기 위한
fixture입니다.

```sh
NEIS_FIXTURE_MODE=true uv run bsl-mcp
```

MCP endpoint는 `http://localhost:8001/mcp`입니다. 별도 터미널에서 Inspector를
실행한 뒤 이 URL에 연결합니다.

```sh
npx -y @modelcontextprotocol/inspector
```

테스트는 다음과 같이 실행합니다.

```sh
uv run pytest
```