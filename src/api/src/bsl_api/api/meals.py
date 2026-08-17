"""`GET /api/v1/schools/{schoolCode}/meals`."""

from __future__ import annotations

from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query

from bsl_api.clients.base import SchoolAndMealClient
from bsl_api.dependencies import get_neis_client
from bsl_api.models.schemas import MealRangeResponse
from bsl_api.services.meals import get_school_meals

router = APIRouter(tags=["Meals"])


@router.get(
    "/schools/{schoolCode}/meals",
    response_model=MealRangeResponse,
    response_model_by_alias=True,
)
async def get_meals(
    school_code: Annotated[str, Path(alias="schoolCode", min_length=1, max_length=20)],
    office_code: Annotated[str, Query(alias="officeCode", min_length=1, max_length=20)],
    from_date: Annotated[date, Query(alias="from")],
    to_date: Annotated[date, Query(alias="to")],
    client: Annotated[SchoolAndMealClient, Depends(get_neis_client)],
) -> MealRangeResponse:
    return await get_school_meals(
        client,
        school_code=school_code,
        office_code=office_code,
        from_date=from_date,
        to_date=to_date,
    )
