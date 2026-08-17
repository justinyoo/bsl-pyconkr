"""내부 OpenAPI 계약(`src/openapi.json`)에 대응하는 Pydantic 응답 모델."""

from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: Literal["ok"] = "ok"


class SchoolSummary(BaseModel):
    school_code: str = Field(serialization_alias="schoolCode")
    education_office_code: str = Field(serialization_alias="educationOfficeCode")
    school_name: str = Field(serialization_alias="schoolName")
    education_office_name: str = Field(serialization_alias="educationOfficeName")
    location_name: str | None = Field(serialization_alias="locationName")
    school_type: str | None = Field(serialization_alias="schoolType")

    model_config = {"populate_by_name": True}


class SchoolSearchResponse(BaseModel):
    items: list[SchoolSummary]
    total: int


class SelectedSchool(BaseModel):
    school_code: str = Field(serialization_alias="schoolCode")
    education_office_code: str = Field(serialization_alias="educationOfficeCode")
    school_name: str = Field(serialization_alias="schoolName")
    education_office_name: str = Field(serialization_alias="educationOfficeName")

    model_config = {"populate_by_name": True}


class Meal(BaseModel):
    date: date
    meal_type: Literal["lunch"] = Field(
        default="lunch", serialization_alias="mealType"
    )
    dishes: list[str]
    origins: list[str]
    nutrition: list[str]
    calories: str | None
    serving_count: int | None = Field(serialization_alias="servingCount")

    model_config = {"populate_by_name": True}


class MealRangeResponse(BaseModel):
    school: SelectedSchool
    from_: date = Field(serialization_alias="from")
    to: date
    meals: list[Meal]

    model_config = {"populate_by_name": True}
