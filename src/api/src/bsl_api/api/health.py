"""`GET /api/v1/health`."""

from __future__ import annotations

from fastapi import APIRouter

from bsl_api.models.schemas import HealthResponse

router = APIRouter(tags=["Health"])


@router.get("/health", response_model=HealthResponse)
async def get_health() -> HealthResponse:
    return HealthResponse()
