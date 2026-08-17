"""`GET /api/v1/schools`."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from bsl_api.clients.base import SchoolAndMealClient
from bsl_api.dependencies import get_neis_client
from bsl_api.errors import InvalidRequestError
from bsl_api.models.schemas import SchoolSearchResponse
from bsl_api.services.schools import search_schools

router = APIRouter(tags=["Schools"])


@router.get("/schools", response_model=SchoolSearchResponse)
async def get_schools(
    name: Annotated[str, Query(min_length=1, max_length=100)],
    client: Annotated[SchoolAndMealClient, Depends(get_neis_client)],
) -> SchoolSearchResponse:
    trimmed = name.strip()
    if len(trimmed) < 2:
        raise InvalidRequestError(
            "검색어는 공백을 제거한 후 2자 이상이어야 합니다.",
            errors={"name": ["검색어는 2자 이상 입력해 주세요."]},
        )
    return await search_schools(client, trimmed)
