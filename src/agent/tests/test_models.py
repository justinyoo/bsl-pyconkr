from datetime import date, timedelta

import pytest
from pydantic import ValidationError

from bsl_agent.models import EvaluationRequest, School


def _school(code: str) -> School:
    return School(
        school_code=code,
        education_office_code="B10",
        school_name=code,
        education_office_name="서울특별시교육청",
        location_name="서울특별시",
        school_type="고등학교",
    )


def test_evaluation_request_requires_two_different_schools() -> None:
    with pytest.raises(ValidationError, match="서로 다른"):
        EvaluationRequest(
            schools=[_school("same"), _school("same")],
            date=date.today(),
            prompt="비교",
        )


def test_evaluation_request_rejects_future_date() -> None:
    with pytest.raises(ValidationError, match="직전 달 1일"):
        EvaluationRequest(
            schools=[_school("one"), _school("two")],
            date=date.today() + timedelta(days=1),
            prompt="비교",
        )
