"""에이전트 앱의 입력, MCP 데이터 및 최종 평가 모델."""

from __future__ import annotations

from datetime import date, datetime
from typing import Annotated, Literal
from zoneinfo import ZoneInfo

from pydantic import BaseModel, ConfigDict, Field, model_validator

_KST = ZoneInfo("Asia/Seoul")


def _camel_case(value: str) -> str:
    first, *rest = value.split("_")
    return first + "".join(part.capitalize() for part in rest)


class ApiModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=_camel_case,
        populate_by_name=True,
        serialize_by_alias=True,
    )


class School(ApiModel):
    school_code: str
    education_office_code: str
    school_name: str
    education_office_name: str
    location_name: str | None
    school_type: str | None


class SchoolSearchResult(ApiModel):
    schools: list[School]
    total: int


class Meal(ApiModel):
    date: date
    meal_type: Literal["lunch"] = "lunch"
    dishes: list[str]
    origins: list[str]
    nutrition: list[str]
    calories: str | None
    serving_count: int | None


class SchoolMealsResult(ApiModel):
    school: School
    from_date: date
    to_date: date
    meals: list[Meal]


class EvaluationRequest(ApiModel):
    schools: Annotated[list[School], Field(min_length=2, max_length=2)]
    date: date
    prompt: Annotated[str, Field(min_length=1, max_length=4000)]

    @model_validator(mode="after")
    def validate_selection(self) -> "EvaluationRequest":
        if self.schools[0].school_code == self.schools[1].school_code:
            raise ValueError("서로 다른 두 학교를 선택해야 합니다.")
        today = datetime.now(tz=_KST).date()
        earliest = (
            date(today.year - 1, 12, 1)
            if today.month == 1
            else date(today.year, today.month - 1, 1)
        )
        if self.date < earliest or self.date > today:
            raise ValueError("평가 날짜는 직전 달 1일부터 오늘 사이여야 합니다.")
        return self


class EvaluationContext(ApiModel):
    request: EvaluationRequest
    meals: Annotated[list[SchoolMealsResult], Field(min_length=2, max_length=2)]


CriterionId = Literal["nutrition_balance", "healthiness", "menu_quality"]


class SchoolCriterionEvaluation(ApiModel):
    school_code: str
    rating: Annotated[int, Field(ge=1, le=5)]
    evidence: Annotated[list[str], Field(min_length=1)]
    limitations: list[str] = Field(default_factory=list)
    improvements: Annotated[list[str], Field(min_length=1)]


class CriterionEvaluation(ApiModel):
    criterion: CriterionId
    evaluations: Annotated[
        list[SchoolCriterionEvaluation], Field(min_length=2, max_length=2)
    ]


class WeightedCriterionResult(ApiModel):
    criterion: CriterionId
    rating: int
    weight: int
    weighted_score: float
    evidence: list[str]
    limitations: list[str]
    improvements: list[str]


class SchoolScore(ApiModel):
    school: School
    criteria: Annotated[
        list[WeightedCriterionResult], Field(min_length=3, max_length=3)
    ]
    total_score: float


Outcome = Literal["first", "second", "tie"]


class ScoredEvaluation(ApiModel):
    date: date
    school_scores: Annotated[list[SchoolScore], Field(min_length=2, max_length=2)]
    outcome: Outcome


class FinalNarrative(ApiModel):
    summary: Annotated[str, Field(min_length=1)]
    key_reasons: Annotated[list[str], Field(min_length=1)]
    improvements: dict[str, list[str]]
    warnings: list[str] = Field(default_factory=list)


class BattleEvaluation(ApiModel):
    date: date
    school_scores: Annotated[list[SchoolScore], Field(min_length=2, max_length=2)]
    outcome: Outcome
    winner_school_code: str | None
    summary: str
    key_reasons: list[str]
    improvements: dict[str, list[str]]
    warnings: list[str]
