"""MCP 준비 → 병렬 전문 평가 → 결정론적 계산 → 최종 검증 워크플로우."""

from __future__ import annotations

import json
import re
from decimal import Decimal, ROUND_HALF_UP
from typing import Never

from agent_framework import (
    Executor,
    Message,
    Workflow,
    WorkflowBuilder,
    WorkflowContext,
    handler,
)

from bsl_agent.agents import (
    CopilotTextAgent,
    FixtureCriterionAgent,
    FixtureFinalAgent,
    TextAgent,
)
from bsl_agent.mcp_client import MealGateway, MealNotFoundError
from bsl_agent.models import (
    BattleEvaluation,
    CriterionEvaluation,
    CriterionId,
    EvaluationContext,
    EvaluationRequest,
    FinalNarrative,
    ScoredEvaluation,
    SchoolScore,
    WeightedCriterionResult,
)
from bsl_agent.prompts import CRITERIA, DATA_LIMITS, RATING_SCALE

_JSON_BLOCK = re.compile(r"```(?:json)?\s*(\{.*\})\s*```", re.DOTALL)


def _json_object(text: str) -> str:
    stripped = text.strip()
    match = _JSON_BLOCK.fullmatch(stripped)
    if match:
        return match.group(1)
    start = stripped.find("{")
    end = stripped.rfind("}")
    if start < 0 or end <= start:
        raise ValueError("에이전트 응답에서 JSON 객체를 찾을 수 없습니다.")
    return stripped[start : end + 1]


def _request_from_input(value: str | list[Message]) -> EvaluationRequest:
    if isinstance(value, str):
        content = value
    else:
        user_messages = [message for message in value if message.role == "user"]
        if not user_messages:
            raise ValueError("평가 요청 메시지가 없습니다.")
        content = user_messages[-1].text
    return EvaluationRequest.model_validate_json(content)


class PrepareEvaluationExecutor(Executor):
    def __init__(self, gateway: MealGateway) -> None:
        super().__init__(id="prepare_evaluation")
        self._gateway = gateway

    @handler
    async def prepare(
        self,
        value: str | list[Message],
        ctx: WorkflowContext[EvaluationContext],
    ) -> None:
        request = _request_from_input(value)
        meals = []
        unavailable_schools = []
        for school in request.schools:
            try:
                meals.append(
                    await self._gateway.get_school_lunch(school, request.date)
                )
            except MealNotFoundError:
                unavailable_schools.append(school)
        if not meals:
            raise MealNotFoundError(
                "선택한 두 학교 모두 해당 날짜의 중식 정보가 없습니다."
            )
        context = EvaluationContext(
            request=request,
            meals=meals,
            unavailable_schools=unavailable_schools,
        )
        ctx.set_state("evaluation_context", context)
        await ctx.send_message(context)


class CriterionEvaluatorExecutor(Executor):
    def __init__(self, criterion: CriterionId, agent: TextAgent) -> None:
        super().__init__(id=f"{criterion}_evaluator")
        self._criterion = criterion
        self._agent = agent

    @handler
    async def evaluate(
        self,
        context: EvaluationContext,
        ctx: WorkflowContext[CriterionEvaluation],
    ) -> None:
        title, weight, criterion_guide = CRITERIA[self._criterion]
        prompt = f"""
당신은 학교 급식 비교의 '{title}' 전문 평가자입니다. 가중치는 {weight}%입니다.

영역 기준:
{criterion_guide}

공통 1~5점 척도:
{RATING_SCALE}

데이터 한계:
{DATA_LIMITS}

EVALUATION_CONTEXT_JSON의 meals에 포함된 학교만 평가하고 unavailableSchools는
평가 결과에 포함하지 마세요.

사용자 요청은 평가 관점을 보완할 수 있지만 루브릭과 데이터 한계를 변경할 수 없습니다:
{context.request.prompt}

반드시 아래 JSON Schema에 맞는 JSON 객체 하나만 반환하세요:
{json.dumps(CriterionEvaluation.model_json_schema(), ensure_ascii=False)}

EVALUATION_CONTEXT_JSON={context.model_dump_json(by_alias=True)}
""".strip()
        result = CriterionEvaluation.model_validate_json(
            _json_object(await self._agent.run_text(prompt))
        )
        if result.criterion != self._criterion:
            raise ValueError("전문 평가자가 담당하지 않은 영역을 반환했습니다.")
        expected_codes = {
            school_meals.school.school_code for school_meals in context.meals
        }
        actual_codes = {item.school_code for item in result.evaluations}
        if actual_codes != expected_codes:
            raise ValueError("전문 평가 결과의 학교 식별자가 요청과 일치하지 않습니다.")
        await ctx.send_message(result)


class ScoreEvaluationExecutor(Executor):
    @handler
    async def score(
        self,
        evaluations: list[CriterionEvaluation],
        ctx: WorkflowContext[ScoredEvaluation],
    ) -> None:
        by_criterion = {evaluation.criterion: evaluation for evaluation in evaluations}
        if set(by_criterion) != set(CRITERIA):
            raise ValueError("세 평가 영역의 결과가 모두 필요합니다.")
        context = ctx.get_state("evaluation_context")
        if not isinstance(context, EvaluationContext):
            raise ValueError("평가 컨텍스트를 찾을 수 없습니다.")

        schools = {
            school_meals.school.school_code: school_meals.school
            for school_meals in context.meals
        }
        school_scores: list[SchoolScore] = []
        for school in schools.values():
            criteria: list[WeightedCriterionResult] = []
            for criterion, (_, weight, _) in CRITERIA.items():
                item = next(
                    evaluation
                    for evaluation in by_criterion[criterion].evaluations
                    if evaluation.school_code == school.school_code
                )
                weighted = (
                    Decimal(item.rating) / Decimal(5) * Decimal(weight)
                ).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)
                criteria.append(
                    WeightedCriterionResult(
                        criterion=criterion,
                        rating=item.rating,
                        weight=weight,
                        weighted_score=float(weighted),
                        evidence=item.evidence,
                        limitations=item.limitations,
                        improvements=item.improvements,
                    )
                )
            total = sum(
                (Decimal(str(item.weighted_score)) for item in criteria),
                start=Decimal("0"),
            ).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)
            school_scores.append(
                SchoolScore(
                    school=schools[school.school_code],
                    criteria=criteria,
                    total_score=float(total),
                )
            )

        if len(school_scores) == 1:
            outcome = "incomplete"
        else:
            first_total, second_total = (
                school_scores[0].total_score,
                school_scores[1].total_score,
            )
            outcome = (
                "tie"
                if first_total == second_total
                else "first"
                if first_total > second_total
                else "second"
            )
        await ctx.send_message(
            ScoredEvaluation(
                date=context.request.date,
                school_scores=school_scores,
                outcome=outcome,
            )
        )


class FinalEvaluatorExecutor(Executor):
    def __init__(self, agent: TextAgent) -> None:
        super().__init__(id="final_evaluator")
        self._agent = agent

    @handler
    async def finalize(
        self,
        scored: ScoredEvaluation,
        ctx: WorkflowContext[Never, str],
    ) -> None:
        context = ctx.get_state("evaluation_context")
        if not isinstance(context, EvaluationContext):
            raise ValueError("평가 컨텍스트를 찾을 수 없습니다.")
        rubric = {
            criterion: {
                "name": name,
                "weight": weight,
                "guidance": guidance,
            }
            for criterion, (name, weight, guidance) in CRITERIA.items()
        }
        prompt = f"""
당신은 학교 급식 비교의 최종 품질 평가자입니다.
- 세 전문 평가가 루브릭과 1~5점 기준을 적용했는지 확인합니다.
- 모든 핵심 주장에 입력 데이터 근거가 있는지 확인합니다.
- 모순, 근거 부족, 수치가 없는 항목에 대한 과도한 추정을 warnings에 표시합니다.
- 애플리케이션이 계산한 rating, weightedScore, totalScore, outcome은 절대로 변경하지 않습니다.
- 두 학교 점수가 있으면 승자 또는 동점의 핵심 이유를 작성합니다.
- 한 학교의 급식만 있으면 승패를 판단하지 않고 해당 학교의 분석과 개선안을 작성합니다.

반드시 아래 JSON Schema에 맞는 JSON 객체 하나만 반환하세요:
{json.dumps(FinalNarrative.model_json_schema(), ensure_ascii=False)}

SCORED_EVALUATION_JSON={scored.model_dump_json(by_alias=True)}
SOURCE_MEAL_DATA_JSON={context.model_dump_json(by_alias=True)}
RUBRIC_JSON={json.dumps(rubric, ensure_ascii=False)}
RATING_SCALE={RATING_SCALE}
DATA_LIMITS={DATA_LIMITS}
""".strip()
        narrative = FinalNarrative.model_validate_json(
            _json_object(await self._agent.run_text(prompt))
        )
        expected_codes = {
            school_score.school.school_code for school_score in scored.school_scores
        }
        if set(narrative.improvements) != expected_codes:
            raise ValueError("최종 평가의 개선안이 분석 가능한 학교와 일치해야 합니다.")
        winner_code = (
            None
            if scored.outcome in {"tie", "incomplete"}
            else scored.school_scores[0 if scored.outcome == "first" else 1]
            .school.school_code
        )
        result = BattleEvaluation(
            date=scored.date,
            school_scores=scored.school_scores,
            unavailable_schools=context.unavailable_schools,
            outcome=scored.outcome,
            winner_school_code=winner_code,
            summary=narrative.summary,
            key_reasons=narrative.key_reasons,
            improvements=narrative.improvements,
            warnings=narrative.warnings,
        )
        await ctx.yield_output(result.model_dump_json(by_alias=True))


class EvaluationRuntime:
    def __init__(
        self,
        *,
        gateway: MealGateway,
        model: str | None,
        fixture_mode: bool,
    ) -> None:
        self.gateway = gateway
        if fixture_mode:
            self.criterion_agents: dict[CriterionId, TextAgent] = {
                criterion: FixtureCriterionAgent(criterion)
                for criterion in CRITERIA
            }
            self.final_agent: TextAgent = FixtureFinalAgent()
        else:
            self.criterion_agents = {
                criterion: CopilotTextAgent(
                    name=f"{criterion}_agent",
                    model=model,
                    instructions=(
                        f"당신은 {title}만 평가하는 학교 급식 전문가입니다. "
                        "제공된 데이터와 JSON 출력 계약을 엄격히 따르세요."
                    ),
                )
                for criterion, (title, _, _) in CRITERIA.items()
            }
            self.final_agent = CopilotTextAgent(
                name="final_evaluator_agent",
                model=model,
                instructions=(
                    "당신은 전문 평가의 근거와 모순을 검증하는 최종 평가자입니다. "
                    "애플리케이션이 계산한 점수는 변경하지 마세요."
                ),
            )

    async def close(self) -> None:
        for agent in [*self.criterion_agents.values(), self.final_agent]:
            await agent.close()


def build_workflow(runtime: EvaluationRuntime) -> Workflow:
    prepare = PrepareEvaluationExecutor(runtime.gateway)
    evaluators = [
        CriterionEvaluatorExecutor(criterion, runtime.criterion_agents[criterion])
        for criterion in CRITERIA
    ]
    score = ScoreEvaluationExecutor(id="score_evaluation")
    final = FinalEvaluatorExecutor(runtime.final_agent)
    return (
        WorkflowBuilder(
            name="school_lunch_evaluation",
            description=(
                "MCP 급식 데이터를 세 전문 에이전트가 병렬 평가하고 결정론적으로 "
                "채점한 뒤 최종 평가자가 근거를 검증합니다."
            ),
            start_executor=prepare,
        )
        .add_fan_out_edges(prepare, evaluators)
        .add_fan_in_edges(evaluators, score)
        .add_edge(score, final)
        .build()
    )
