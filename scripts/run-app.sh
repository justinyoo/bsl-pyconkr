#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd -- "${SCRIPT_DIR}/.." && pwd)"
BACKEND_PID=""
FRONTEND_PID=""
MCP_PID=""
AGENT_PID=""
DEVUI_PID=""

load_dotenv() {
  local env_file="$1"
  local key value

  [[ -f "${env_file}" ]] || return 0

  while IFS='=' read -r key value; do
    key="${key#"${key%%[![:space:]]*}"}"
    key="${key%"${key##*[![:space:]]}"}"
    [[ -z "${key}" || "${key}" == \#* ]] && continue
    [[ "${key}" =~ ^[A-Za-z_][A-Za-z0-9_]*$ ]] || continue
    [[ -n "${!key+x}" ]] && continue

    value="${value%$'\r'}"
    if [[ "${value}" =~ ^\".*\"$ || "${value}" =~ ^\'.*\'$ ]]; then
      value="${value:1:${#value}-2}"
    fi
    export "${key}=${value}"
  done < "${env_file}"
}

stop_process_tree() {
  local pid="$1"
  local child

  [[ -n "${pid}" ]] || return
  for child in $(pgrep -P "${pid}" 2>/dev/null || true); do
    stop_process_tree "${child}"
  done
  kill -TERM "${pid}" 2>/dev/null || true
}

cleanup() {
  trap - EXIT INT TERM
  stop_process_tree "${FRONTEND_PID}"
  stop_process_tree "${BACKEND_PID}"
  stop_process_tree "${MCP_PID}"
  stop_process_tree "${AGENT_PID}"
  stop_process_tree "${DEVUI_PID}"
  [[ -z "${FRONTEND_PID}" ]] || wait "${FRONTEND_PID}" 2>/dev/null || true
  [[ -z "${BACKEND_PID}" ]] || wait "${BACKEND_PID}" 2>/dev/null || true
  [[ -z "${MCP_PID}" ]] || wait "${MCP_PID}" 2>/dev/null || true
  [[ -z "${AGENT_PID}" ]] || wait "${AGENT_PID}" 2>/dev/null || true
  [[ -z "${DEVUI_PID}" ]] || wait "${DEVUI_PID}" 2>/dev/null || true
}

trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

load_dotenv "${REPO_ROOT}/.env"

BACKEND_PORT="${BACKEND_PORT:-8000}"
FRONTEND_PORT="${FRONTEND_PORT:-5173}"
MCP_PORT="${MCP_PORT:-8001}"
AGENT_PORT="${AGENT_PORT:-8002}"
AGENT_DEVUI_PORT="${AGENT_DEVUI_PORT:-8080}"
export VITE_BACKEND_ORIGIN="${VITE_BACKEND_ORIGIN:-http://localhost:${BACKEND_PORT}}"
export VITE_AGENT_ORIGIN="${VITE_AGENT_ORIGIN:-http://localhost:${AGENT_PORT}}"
export MCP_SERVER_URL="${MCP_SERVER_URL:-http://localhost:${MCP_PORT}/mcp}"
export AGENT_FIXTURE_MODE="${AGENT_FIXTURE_MODE:-${NEIS_FIXTURE_MODE:-false}}"

if [[ -z "${NEIS_API_KEY:-}" && "${NEIS_FIXTURE_MODE:-false}" != "true" ]]; then
  echo "NEIS_API_KEY를 설정하거나 NEIS_FIXTURE_MODE=true를 지정하세요." >&2
  exit 1
fi

if [[ ! -d "${REPO_ROOT}/src/web/node_modules" ]]; then
  echo "==> 프론트엔드 의존성 설치"
  (cd "${REPO_ROOT}/src/web" && npm ci)
fi

echo "==> 백엔드 시작: http://localhost:${BACKEND_PORT}"
(
  cd "${REPO_ROOT}/src/api"
  exec uv run fastapi dev src/bsl_api/main.py --host 0.0.0.0 \
    --port "${BACKEND_PORT}"
) &
BACKEND_PID=$!

echo "==> MCP 서버 시작: http://localhost:${MCP_PORT}/mcp"
(
  cd "${REPO_ROOT}/src/mcp"
  export MCP_PORT
  exec uv run bsl-mcp
) &
MCP_PID=$!

echo "==> 에이전트 앱 시작: http://localhost:${AGENT_PORT}"
(
  cd "${REPO_ROOT}/src/agent"
  export AGENT_PORT MCP_SERVER_URL AGENT_FIXTURE_MODE
  exec uv run bsl-agent
) &
AGENT_PID=$!

echo "==> Agent Framework DevUI 시작: http://localhost:${AGENT_DEVUI_PORT}"
(
  cd "${REPO_ROOT}/src/agent"
  export AGENT_DEVUI_PORT MCP_SERVER_URL AGENT_FIXTURE_MODE
  exec uv run bsl-agent-devui
) &
DEVUI_PID=$!

echo "==> 프론트엔드 시작: http://localhost:${FRONTEND_PORT}"
(
  cd "${REPO_ROOT}/src/web"
  exec npm run dev -- --host 0.0.0.0 --port "${FRONTEND_PORT}"
) &
FRONTEND_PID=$!

echo "CTRL+C를 누르면 모든 앱을 종료합니다."

while kill -0 "${BACKEND_PID}" 2>/dev/null &&
  kill -0 "${MCP_PID}" 2>/dev/null &&
  kill -0 "${AGENT_PID}" 2>/dev/null &&
  kill -0 "${DEVUI_PID}" 2>/dev/null &&
  kill -0 "${FRONTEND_PID}" 2>/dev/null; do
  sleep 1
done

if ! kill -0 "${BACKEND_PID}" 2>/dev/null; then
  wait "${BACKEND_PID}"
elif ! kill -0 "${MCP_PID}" 2>/dev/null; then
  wait "${MCP_PID}"
elif ! kill -0 "${AGENT_PID}" 2>/dev/null; then
  wait "${AGENT_PID}"
elif ! kill -0 "${DEVUI_PID}" 2>/dev/null; then
  wait "${DEVUI_PID}"
else
  wait "${FRONTEND_PID}"
fi
