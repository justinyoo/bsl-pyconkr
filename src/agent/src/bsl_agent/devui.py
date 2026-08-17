"""Agent Framework DevUI 전용 로컬 개발 진입점."""

from agent_framework.devui import serve
from agent_framework_devui import register_cleanup

from bsl_agent.mcp_client import McpMealGateway
from bsl_agent.settings import get_settings
from bsl_agent.workflow import EvaluationRuntime, build_workflow


def main() -> None:
    settings = get_settings()
    runtime = EvaluationRuntime(
        gateway=McpMealGateway(settings.mcp_server_url),
        model=settings.copilot_model,
        fixture_mode=settings.agent_fixture_mode,
    )
    workflow = build_workflow(runtime)
    register_cleanup(workflow, runtime.close)
    serve(
        entities=[workflow],
        host="127.0.0.1",
        port=settings.agent_devui_port,
        auto_open=False,
        cors_origins=settings.allowed_origins,
        instrumentation_enabled=True,
        auth_enabled=False,
    )
