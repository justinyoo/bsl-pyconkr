"""MCP 도구의 구조화된 출력 모델."""

from datetime import date
from typing import Literal

from pydantic import BaseModel


class School(BaseModel):
    school_code: str
    education_office_code: str
    school_name: str
    education_office_name: str
    location_name: str | None
    school_type: str | None


class SchoolSearchResult(BaseModel):
    schools: list[School]
    total: int


class Meal(BaseModel):
    date: date
    meal_type: Literal["lunch"] = "lunch"
    dishes: list[str]
    origins: list[str]
    nutrition: list[str]
    calories: str | None
    serving_count: int | None


class SchoolMealsResult(BaseModel):
    school: School
    from_date: date
    to_date: date
    meals: list[Meal]
