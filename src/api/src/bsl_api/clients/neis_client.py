"""NEIS 공개 API(`data/openapi.json`) 호출 전용 클라이언트.

라우터와 분리된 계층으로, `search_schools`/`get_lunches`는 원본 NEIS 필드를
그대로 담은 딕셔너리 목록을 반환한다. 외부 필드에서 내부 모델로의 변환은
`bsl_api.services`가 담당한다.
"""

from __future__ import annotations

from typing import Any

import httpx

from bsl_api.clients.exceptions import (
    NeisAuthenticationError,
    NeisRateLimitedError,
    NeisUnavailableError,
    NeisUpstreamError,
)

_SCHOOL_INFO_PATH = "/hub/schoolInfo"
_MEAL_SERVICE_PATH = "/hub/mealServiceDietInfo"

# NEIS는 요청 위치 오류 시 코드에 "INFO-"/"ERROR-" 접두어를 붙이는 문서와
# 접두어 없이 숫자만 반환하는 문서가 모두 존재해 두 형태를 모두 처리한다.
_NO_DATA_CODES = {"200"}
_RATE_LIMITED_CODES = {"337", "336"}
_AUTH_ERROR_CODES = {"100", "290", "300"}
_SUCCESS_CODES = {"000"}


def _normalize_code(code: str) -> str:
    return code.rsplit("-", maxsplit=1)[-1]


class NeisClient:
    """NEIS `/hub/schoolInfo`, `/hub/mealServiceDietInfo`를 호출한다."""

    def __init__(
        self,
        *,
        base_url: str,
        api_key: str,
        timeout_seconds: float,
        page_size: int = 100,
    ) -> None:
        self._base_url = base_url
        self._api_key = api_key
        self._timeout_seconds = timeout_seconds
        self._page_size = page_size

    def _client(self) -> httpx.AsyncClient:
        return httpx.AsyncClient(
            base_url=self._base_url, timeout=self._timeout_seconds
        )

    async def _get(self, path: str, params: dict[str, Any]) -> dict[str, Any]:
        request_params = {
            "KEY": self._api_key,
            "Type": "json",
            "pIndex": 1,
            "pSize": self._page_size,
            **params,
        }
        try:
            async with self._client() as client:
                response = await client.get(path, params=request_params)
        except httpx.TimeoutException as exc:
            raise NeisUnavailableError("NEIS 요청이 시간 초과되었습니다.") from exc
        except httpx.ConnectError as exc:
            raise NeisUnavailableError("NEIS에 연결할 수 없습니다.") from exc
        except httpx.HTTPError as exc:
            raise NeisUnavailableError("NEIS 요청 중 알 수 없는 오류가 발생했습니다.") from exc

        if response.status_code >= 500:
            raise NeisUnavailableError(
                f"NEIS가 서버 오류({response.status_code})를 반환했습니다."
            )
        if response.status_code >= 400:
            raise NeisUpstreamError(
                f"NEIS가 클라이언트 오류({response.status_code})를 반환했습니다."
            )

        try:
            return response.json()
        except ValueError as exc:
            raise NeisUpstreamError("NEIS 응답을 파싱할 수 없습니다.") from exc

    @staticmethod
    def _extract_result_code(payload: dict[str, Any]) -> str | None:
        result = payload.get("RESULT")
        if isinstance(result, dict):
            code = result.get("CODE")
            if isinstance(code, str):
                return _normalize_code(code)
        return None

    def _raise_for_result_code(self, code: str) -> None:
        if code in _RATE_LIMITED_CODES:
            raise NeisRateLimitedError("NEIS 요청 한도를 초과했습니다.")
        if code in _AUTH_ERROR_CODES:
            raise NeisAuthenticationError("NEIS 인증키가 유효하지 않습니다.")
        raise NeisUpstreamError(f"NEIS가 처리할 수 없는 요청입니다(코드 {code}).")

    def _extract_rows(
        self, payload: dict[str, Any], root_key: str
    ) -> list[dict[str, Any]]:
        """`head`/`row` 배열에서 원본 NEIS 행을 추출한다.

        데이터가 없거나 오류인 경우 최상위 `RESULT`만 반환되므로 먼저 확인한다.
        """

        top_level_code = self._extract_result_code(payload)
        if top_level_code is not None:
            if top_level_code in _NO_DATA_CODES:
                return []
            self._raise_for_result_code(top_level_code)

        sections = payload.get(root_key)
        if not isinstance(sections, list):
            raise NeisUpstreamError("NEIS 응답 구조가 예상과 다릅니다.")

        rows: list[dict[str, Any]] = []
        for section in sections:
            if not isinstance(section, dict):
                continue
            if "row" in section:
                section_rows = section.get("row") or []
                rows.extend(row for row in section_rows if isinstance(row, dict))
            elif "head" in section:
                head_items = section.get("head") or []
                for head_item in head_items:
                    if isinstance(head_item, dict) and "RESULT" in head_item:
                        code = self._extract_result_code(head_item)
                        if code is not None and code not in _SUCCESS_CODES | _NO_DATA_CODES:
                            self._raise_for_result_code(code)
        return rows

    async def search_schools(self, name: str) -> list[dict[str, Any]]:
        """`SCHUL_NM` 부분 검색으로 학교 기본 정보를 조회한다."""

        payload = await self._get(_SCHOOL_INFO_PATH, {"SCHUL_NM": name})
        return self._extract_rows(payload, "schoolInfo")

    async def get_school(
        self, *, office_code: str, school_code: str
    ) -> list[dict[str, Any]]:
        """교육청 코드와 행정표준코드로 단일 학교 기본 정보를 조회한다."""

        payload = await self._get(
            _SCHOOL_INFO_PATH,
            {
                "ATPT_OFCDC_SC_CODE": office_code,
                "SD_SCHUL_CODE": school_code,
            },
        )
        return self._extract_rows(payload, "schoolInfo")

    async def get_lunches(
        self,
        *,
        office_code: str,
        school_code: str,
        from_ymd: str,
        to_ymd: str,
    ) -> list[dict[str, Any]]:
        """중식(`MMEAL_SC_CODE=2`) 급식 정보를 날짜 범위로 조회한다."""

        payload = await self._get(
            _MEAL_SERVICE_PATH,
            {
                "ATPT_OFCDC_SC_CODE": office_code,
                "SD_SCHUL_CODE": school_code,
                "MMEAL_SC_CODE": "2",
                "MLSV_FROM_YMD": from_ymd,
                "MLSV_TO_YMD": to_ymd,
            },
        )
        return self._extract_rows(payload, "mealServiceDietInfo")
