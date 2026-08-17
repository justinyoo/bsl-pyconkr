"""NEIS 공개 API 클라이언트와 테스트·데모용 fixture 구현."""

from __future__ import annotations

import logging
from datetime import date, datetime, timedelta
from typing import Any, Protocol

import httpx

from bsl_mcp.exceptions import (
    NeisAuthenticationError,
    NeisRateLimitedError,
    NeisResponseError,
    NeisUnavailableError,
)

_LOGGER = logging.getLogger("bsl_mcp.neis")
_NO_DATA_CODES = {"200"}
_SUCCESS_CODES = {"000"}
_RATE_LIMITED_CODES = {"336", "337"}
_AUTH_ERROR_CODES = {"100", "290", "300"}


class SchoolAndMealClient(Protocol):
    async def search_schools(self, name: str) -> list[dict[str, Any]]: ...

    async def get_school(
        self, *, education_office_code: str, school_code: str
    ) -> list[dict[str, Any]]: ...

    async def get_lunches(
        self,
        *,
        education_office_code: str,
        school_code: str,
        from_ymd: str,
        to_ymd: str,
    ) -> list[dict[str, Any]]: ...


def _normalize_code(code: str) -> str:
    return code.rsplit("-", maxsplit=1)[-1]


class NeisClient:
    """`data/openapi.json`의 학교 기본 정보와 급식 식단 API를 호출한다."""

    def __init__(
        self, *, base_url: str, api_key: str, timeout_seconds: float
    ) -> None:
        self._base_url = base_url
        self._api_key = api_key
        self._timeout_seconds = timeout_seconds

    async def _get(self, path: str, params: dict[str, str]) -> dict[str, Any]:
        request_params = {
            "KEY": self._api_key,
            "Type": "json",
            "pIndex": "1",
            "pSize": "100",
            **params,
        }
        try:
            async with httpx.AsyncClient(
                base_url=self._base_url, timeout=self._timeout_seconds
            ) as client:
                response = await client.get(path, params=request_params)
        except httpx.TimeoutException as exc:
            _LOGGER.warning("NEIS request timed out path=%s", path)
            raise NeisUnavailableError from exc
        except httpx.HTTPError as exc:
            _LOGGER.warning(
                "NEIS request failed path=%s error_type=%s",
                path,
                type(exc).__name__,
            )
            raise NeisUnavailableError from exc

        if response.status_code >= 500:
            raise NeisUnavailableError
        if response.status_code >= 400:
            raise NeisResponseError
        try:
            payload = response.json()
        except ValueError as exc:
            raise NeisResponseError from exc
        if not isinstance(payload, dict):
            raise NeisResponseError
        return payload

    @staticmethod
    def _result_code(value: object) -> str | None:
        if not isinstance(value, dict):
            return None
        result = value.get("RESULT")
        if not isinstance(result, dict):
            return None
        code = result.get("CODE")
        return _normalize_code(code) if isinstance(code, str) else None

    @staticmethod
    def _raise_for_code(code: str) -> None:
        if code in _RATE_LIMITED_CODES:
            raise NeisRateLimitedError
        if code in _AUTH_ERROR_CODES:
            raise NeisAuthenticationError
        raise NeisResponseError

    def _rows(self, payload: dict[str, Any], root_key: str) -> list[dict[str, Any]]:
        top_level_code = self._result_code(payload)
        if top_level_code is not None:
            if top_level_code in _NO_DATA_CODES:
                return []
            self._raise_for_code(top_level_code)

        sections = payload.get(root_key)
        if not isinstance(sections, list):
            raise NeisResponseError

        rows: list[dict[str, Any]] = []
        for section in sections:
            if not isinstance(section, dict):
                continue
            section_rows = section.get("row")
            if isinstance(section_rows, list):
                rows.extend(row for row in section_rows if isinstance(row, dict))
                continue
            head = section.get("head")
            if not isinstance(head, list):
                continue
            for item in head:
                code = self._result_code(item)
                if code is not None and code not in _SUCCESS_CODES | _NO_DATA_CODES:
                    self._raise_for_code(code)
        return rows

    async def search_schools(self, name: str) -> list[dict[str, Any]]:
        payload = await self._get("/hub/schoolInfo", {"SCHUL_NM": name})
        return self._rows(payload, "schoolInfo")

    async def get_school(
        self, *, education_office_code: str, school_code: str
    ) -> list[dict[str, Any]]:
        payload = await self._get(
            "/hub/schoolInfo",
            {
                "ATPT_OFCDC_SC_CODE": education_office_code,
                "SD_SCHUL_CODE": school_code,
            },
        )
        return self._rows(payload, "schoolInfo")

    async def get_lunches(
        self,
        *,
        education_office_code: str,
        school_code: str,
        from_ymd: str,
        to_ymd: str,
    ) -> list[dict[str, Any]]:
        payload = await self._get(
            "/hub/mealServiceDietInfo",
            {
                "ATPT_OFCDC_SC_CODE": education_office_code,
                "SD_SCHUL_CODE": school_code,
                "MMEAL_SC_CODE": "2",
                "MLSV_FROM_YMD": from_ymd,
                "MLSV_TO_YMD": to_ymd,
            },
        )
        return self._rows(payload, "mealServiceDietInfo")


_FIXTURE_SCHOOL = {
    "SD_SCHUL_CODE": "7010001",
    "ATPT_OFCDC_SC_CODE": "B10",
    "SCHUL_NM": "서울고정예시고등학교",
    "ATPT_OFCDC_SC_NM": "서울특별시교육청",
    "LCTN_SC_NM": "서울특별시",
    "SCHUL_KND_SC_NM": "고등학교",
}


class FixtureNeisClient:
    """외부 네트워크 없이 로컬 데모와 통합 테스트용 데이터를 반환한다."""

    async def search_schools(self, name: str) -> list[dict[str, Any]]:
        return [_FIXTURE_SCHOOL] if name in _FIXTURE_SCHOOL["SCHUL_NM"] else []

    async def get_school(
        self, *, education_office_code: str, school_code: str
    ) -> list[dict[str, Any]]:
        if (
            education_office_code == _FIXTURE_SCHOOL["ATPT_OFCDC_SC_CODE"]
            and school_code == _FIXTURE_SCHOOL["SD_SCHUL_CODE"]
        ):
            return [_FIXTURE_SCHOOL]
        return []

    async def get_lunches(
        self,
        *,
        education_office_code: str,
        school_code: str,
        from_ymd: str,
        to_ymd: str,
    ) -> list[dict[str, Any]]:
        if not await self.get_school(
            education_office_code=education_office_code,
            school_code=school_code,
        ):
            return []
        start = datetime.strptime(from_ymd, "%Y%m%d").date()
        end = datetime.strptime(to_ymd, "%Y%m%d").date()
        rows: list[dict[str, Any]] = []
        cursor = start
        while cursor <= end:
            rows.append(self._meal_row(cursor))
            cursor += timedelta(days=1)
        return rows

    @staticmethod
    def _meal_row(meal_date: date) -> dict[str, Any]:
        return {
            "MMEAL_SC_CODE": "2",
            "MLSV_YMD": meal_date.strftime("%Y%m%d"),
            "DDISH_NM": "현미밥<br/>된장찌개<br/>제육볶음",
            "ORPLC_INFO": "쌀: 국내산<br/>배추: 국내산",
            "NTR_INFO": "탄수화물(g): 120.5<br/>단백질(g): 25.3",
            "CAL_INFO": "650 Kcal",
            "MLSV_FGR": "450",
        }
