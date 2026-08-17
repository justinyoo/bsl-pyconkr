# 급식 배틀 에이전트 앱

Microsoft Agent Framework의 fan-out/fan-in graph workflow와 GitHub Copilot SDK
provider를 사용해 두 학교의 중식을 비교합니다.

```sh
uv sync --locked
uv run bsl-agent
```

AG-UI endpoint는 `http://localhost:8002/ag-ui/evaluate`, 무작위 학교 후보 API는
`http://localhost:8002/api/schools/random`, 상태 확인은
`http://localhost:8002/health`입니다.

DevUI는 MCP 서버가 실행 중인 상태에서 별도 터미널로 실행합니다.

```sh
uv run bsl-agent-devui
```

웹 화면과 DevUI는 다음 형식의 동일한 자연어 입력을 사용합니다. 학교는 이름과
지역이 모두 일치하는 MCP 검색 결과가 한 곳일 때만 평가합니다.

```text
2026-08-14의 강신중학교(서울특별시)과 경기고등학교(서울특별시) 중식을 평가 루브릭에 따라 비교해 주세요.
```

실제 Copilot 호출 없이 로컬 통합 테스트를 실행하려면
`AGENT_FIXTURE_MODE=true`를 사용합니다.
