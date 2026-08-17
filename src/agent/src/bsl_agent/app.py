"""FastAPI 기반 AG-UI 에이전트 앱 진입점."""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncIterator

from agent_framework.ag_ui import (
    AgentFrameworkWorkflow,
    add_agent_framework_fastapi_endpoint,
)
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

from bsl_agent.mcp_client import McpMealGateway
from bsl_agent.models import SchoolSearchResult
from bsl_agent.settings import Settings, get_settings
from bsl_agent.workflow import EvaluationRuntime, build_workflow


def create_app(
    settings: Settings | None = None,
    runtime: EvaluationRuntime | None = None,
) -> FastAPI:
    resolved = settings or get_settings()
    evaluation_runtime = runtime or EvaluationRuntime(
        gateway=McpMealGateway(resolved.mcp_server_url),
        model=resolved.copilot_model,
        fixture_mode=resolved.agent_fixture_mode,
    )

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        yield
        await evaluation_runtime.close()

    app = FastAPI(title="급식 배틀 에이전트", lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=resolved.allowed_origins,
        allow_credentials=False,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["Content-Type"],
    )

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/api/schools/random", response_model=SchoolSearchResult)
    async def random_schools(
        count: int = Query(default=10, ge=2, le=10),
    ) -> SchoolSearchResult:
        return await evaluation_runtime.gateway.list_random_schools(count)

    ag_ui_workflow = AgentFrameworkWorkflow(
        workflow_factory=lambda _thread_id: build_workflow(evaluation_runtime),
        name="school_lunch_evaluation",
        description="세 전문 에이전트가 두 학교의 중식을 병렬 비교 평가합니다.",
    )
    add_agent_framework_fastapi_endpoint(
        app=app,
        agent=ag_ui_workflow,
        path="/ag-ui/evaluate",
    )
    return app


app = create_app()


def main() -> None:
    import uvicorn

    settings = get_settings()
    uvicorn.run(
        "bsl_agent.app:app",
        host=settings.agent_host,
        port=settings.agent_port,
        reload=False,
    )
