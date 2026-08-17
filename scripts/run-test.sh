#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd -- "${SCRIPT_DIR}/.." && pwd)"
COMPOSE_PROJECT_NAME="bsl-pyconkr-tests"
TEST_FRONTEND_PORT="${TEST_FRONTEND_PORT:-15173}"
TEST_BACKEND_PORT="${TEST_BACKEND_PORT:-18000}"

cleanup() {
  docker compose --project-name "${COMPOSE_PROJECT_NAME}" down --volumes \
    --remove-orphans >/dev/null 2>&1 || true
}
trap cleanup EXIT

cd "${REPO_ROOT}"

echo "==> 백엔드 테스트"
(
  cd src/api
  uv sync --locked
  uv run pytest
)

echo "==> 프론트엔드 테스트"
(
  cd src/web
  npm ci
  npm test
)

echo "==> E2E 테스트용 애플리케이션 시작"
export NEIS_FIXTURE_MODE=true
export NEIS_API_KEY=
export FRONTEND_PORT="${TEST_FRONTEND_PORT}"
export BACKEND_PORT="${TEST_BACKEND_PORT}"
docker compose --project-name "${COMPOSE_PROJECT_NAME}" up --build --detach \
  --wait --wait-timeout 120

echo "==> Playwright E2E 테스트"
(
  cd src/e2e
  npm ci
  npx playwright install chromium
  E2E_BASE_URL="http://localhost:${TEST_FRONTEND_PORT}" npm test
)
