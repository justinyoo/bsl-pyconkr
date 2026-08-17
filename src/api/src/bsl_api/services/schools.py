"""학교 검색 유스케이스: NEIS 원본 필드를 내부 모델로 정규화한다."""

from __future__ import annotations

from typing import Any

from bsl_api.clients.base import SchoolAndMealClient
from bsl_api.clients.exceptions import (
    NeisAuthenticationError,
    NeisRateLimitedError,
    NeisUnavailableError,
    NeisUpstreamError,
)
from bsl_api.errors import RateLimitedError, UpstreamError, UpstreamUnavailableError
from bsl_api.models.schemas import SchoolSearchResponse, SchoolSummary


def _normalize_school(row: dict[str, Any]) -> SchoolSummary:
    return SchoolSummary(
        school_code=str(row["SD_SCHUL_CODE"]),
        education_office_code=str(row["ATPT_OFCDC_SC_CODE"]),
        school_name=str(row["SCHUL_NM"]),
        education_office_name=str(row["ATPT_OFCDC_SC_NM"]),
        location_name=row.get("LCTN_SC_NM") or None,
        school_type=row.get("SCHUL_KND_SC_NM") or None,
    )


async def search_schools(
    client: SchoolAndMealClient, name: str
) -> SchoolSearchResponse:
    """검색어와 일치하는 학교를 조회하고 내부 모델로 변환한다."""

    try:
        rows = await client.search_schools(name)
    except NeisRateLimitedError as exc:
        raise RateLimitedError(str(exc)) from exc
    except NeisAuthenticationError as exc:
        raise UpstreamError(str(exc)) from exc
    except NeisUpstreamError as exc:
        raise UpstreamError(str(exc)) from exc
    except NeisUnavailableError as exc:
        raise UpstreamUnavailableError(str(exc)) from exc

    items = [_normalize_school(row) for row in rows]
    return SchoolSearchResponse(items=items, total=len(items))
