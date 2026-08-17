"""GitHub Copilot SDK 기반 평가 에이전트와 테스트용 대체 구현."""

from __future__ import annotations

import json
from typing import Protocol

from agent_framework.github import GitHubCopilotAgent, GitHubCopilotOptions

from bsl_agent.models import CriterionId, EvaluationContext


def _json_after_marker(prompt: str, marker: str) -> object:
    value, _ = json.JSONDecoder().raw_decode(prompt.split(marker, 1)[1])
    return value


class TextAgent(Protocol):
    async def run_text(self, prompt: str) -> str: ...

    async def close(self) -> None: ...


class CopilotTextAgent:
    def __init__(
        self,
        *,
        name: str,
        instructions: str,
        model: str | None,
    ) -> None:
        options = GitHubCopilotOptions(model=model) if model else None
        self._agent = GitHubCopilotAgent(
            name=name,
            instructions=instructions,
            default_options=options,
        )

    async def run_text(self, prompt: str) -> str:
        response = await self._agent.run(prompt)
        text = response.text.strip()
        if not text:
            raise ValueError("에이전트가 빈 응답을 반환했습니다.")
        return text

    async def close(self) -> None:
        await self._agent.stop()


class FixtureCriterionAgent:
    def __init__(self, criterion: CriterionId) -> None:
        self._criterion = criterion

    async def run_text(self, prompt: str) -> str:
        marker = "EVALUATION_CONTEXT_JSON="
        context = EvaluationContext.model_validate(
            _json_after_marker(prompt, marker)
        )
        evaluations = []
        for index, school_meals in enumerate(context.meals):
            school = school_meals.school
            evaluations.append(
                {
                    "schoolCode": school.school_code,
                    "rating": 3 + index,
                    "evidence": [
                        f"{school.school_name}의 입력 급식 데이터에 근거한 평가입니다."
                    ],
                    "limitations": ["fixture 모드의 결정적 평가입니다."],
                    "improvements": ["부족한 식품군을 보완해 구성을 다양화하세요."],
                }
            )
        return json.dumps(
            {"criterion": self._criterion, "evaluations": evaluations},
            ensure_ascii=False,
        )

    async def close(self) -> None:
        return None


class FixtureFinalAgent:
    async def run_text(self, prompt: str) -> str:
        marker = "SCORED_EVALUATION_JSON="
        payload = _json_after_marker(prompt, marker)
        if not isinstance(payload, dict):
            raise ValueError("fixture 최종 평가 입력이 올바르지 않습니다.")
        incomplete = len(payload["schoolScores"]) == 1
        return json.dumps(
            {
                "summary": (
                    "한 학교의 급식 정보가 없어 가능한 학교만 분석했습니다."
                    if incomplete
                    else "세 평가 영역의 근거와 가중 점수를 종합한 결과입니다."
                ),
                "keyReasons": [
                    (
                        "급식 정보가 있는 학교의 세 평가 영역을 분석했습니다."
                        if incomplete
                        else "영양 균형, 건강성, 메뉴 품질의 가중 점수를 비교했습니다."
                    )
                ],
                "warnings": ["이 평가는 영양사의 전문 진단을 대체하지 않습니다."],
            },
            ensure_ascii=False,
        )

    async def close(self) -> None:
        return None
