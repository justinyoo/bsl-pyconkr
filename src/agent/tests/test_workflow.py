import json
from datetime import date

import pytest
from agent_framework import Message

from bsl_agent.models import (
    BattleEvaluation,
    Meal,
    School,
    SchoolMealsResult,
    SchoolSearchResult,
)
from bsl_agent.workflow import EvaluationRuntime, build_workflow


class FixtureGateway:
    schools = [
        School(
            school_code=f"school-{index}",
            education_office_code="B10",
            school_name=f"예시학교 {index}",
            education_office_name="서울특별시교육청",
            location_name="서울특별시",
            school_type="고등학교",
        )
        for index in range(1, 11)
    ]

    async def list_random_schools(self, count: int = 10) -> SchoolSearchResult:
        return SchoolSearchResult(schools=self.schools[:count], total=count)

    async def get_school_lunch(
        self, school: School, meal_date: date
    ) -> SchoolMealsResult:
        return SchoolMealsResult(
            school=school,
            from_date=meal_date,
            to_date=meal_date,
            meals=[
                Meal(
                    date=meal_date,
                    dishes=["현미밥", "된장찌개", "닭갈비", "시금치나물"],
                    origins=["쌀: 국내산"],
                    nutrition=["단백질(g): 25.3", "나트륨(mg): 820"],
                    calories="650 Kcal",
                    serving_count=450,
                )
            ],
        )


@pytest.mark.anyio
async def test_workflow_runs_three_evaluators_and_preserves_weighted_scores() -> None:
    gateway = FixtureGateway()
    runtime = EvaluationRuntime(gateway=gateway, model=None, fixture_mode=True)
    workflow = build_workflow(runtime)
    request = {
        "schools": [
            gateway.schools[0].model_dump(by_alias=True),
            gateway.schools[1].model_dump(by_alias=True),
        ],
        "date": date.today().isoformat(),
        "prompt": "확인 가능한 정보만 사용해 비교해 주세요.",
    }

    run_result = await workflow.run(
        [Message(role="user", contents=[json.dumps(request)])]
    )
    outputs = run_result.get_outputs()

    assert len(outputs) == 1
    result = BattleEvaluation.model_validate_json(outputs[0])
    assert [item.weight for item in result.school_scores[0].criteria] == [45, 30, 25]
    assert sum(item.weight for item in result.school_scores[0].criteria) == 100
    assert result.school_scores[0].total_score == 60
    assert result.school_scores[1].total_score == 80
    assert result.outcome == "second"
    assert result.winner_school_code == "school-2"


@pytest.mark.anyio
async def test_random_school_gateway_returns_ten_candidates() -> None:
    result = await FixtureGateway().list_random_schools()

    assert result.total == 10
    assert len(result.schools) == 10
