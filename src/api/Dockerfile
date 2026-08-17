# syntax=docker/dockerfile:1
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

WORKDIR /app

ENV UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never \
    PYTHONUNBUFFERED=1

# 의존성 정의 파일을 먼저 복사해 코드 변경 시에도 Docker 캐시를 재사용한다.
COPY pyproject.toml uv.lock ./
RUN uv sync --locked --no-dev --no-install-project

COPY src ./src
RUN uv sync --locked --no-dev

EXPOSE 8000

CMD ["uv", "run", "fastapi", "run", "src/bsl_api/main.py", "--host", "0.0.0.0", "--port", "8000"]
