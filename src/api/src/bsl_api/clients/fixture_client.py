"""E2E 및 데모용 고정 데이터 NEIS 클라이언트.

Docker Compose E2E 실행에서 실제 NEIS API 키 없이도 결정적인 결과를
반환하기 위한 대체 구현이다(TRD 12.5). `NeisClient`와 동일한 메서드
시그니처(`search_schools`/`get_school`/`get_lunches`)를 제공하는 덕타이핑
대체재이며, 서비스 계층은 이 차이를 알 필요가 없다.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Any

_FIXTURE_OFFICE_CODE = "B10"
_FIXTURE_SCHOOL_CODE = "7010001"
_FIXTURE_SCHOOL_NAME = "서울고정예시고등학교"

_FIXTURE_SCHOOLS: list[dict[str, Any]] = [
    {
        "SD_SCHUL_CODE": _FIXTURE_SCHOOL_CODE,
        "ATPT_OFCDC_SC_CODE": _FIXTURE_OFFICE_CODE,
        "SCHUL_NM": _FIXTURE_SCHOOL_NAME,
        "ATPT_OFCDC_SC_NM": "서울특별시교육청",
        "LCTN_SC_NM": "서울특별시",
        "SCHUL_KND_SC_NM": "고등학교",
    },
    {
        "SD_SCHUL_CODE": "7010002",
        "ATPT_OFCDC_SC_CODE": _FIXTURE_OFFICE_CODE,
        "SCHUL_NM": "서울고정예시중학교",
        "ATPT_OFCDC_SC_NM": "서울특별시교육청",
        "LCTN_SC_NM": "서울특별시",
        "SCHUL_KND_SC_NM": "중학교",
    },
]

_FIXTURE_DISHES = ["현미밥", "된장찌개", "제육볶음", "잡채", "배추김치"]


def _ymd(value: date) -> str:
    return value.strftime("%Y%m%d")


class FixtureNeisClient:
    """실제 HTTP 호출 없이 결정적인 학교·급식 데이터를 반환한다."""

    async def search_schools(self, name: str) -> list[dict[str, Any]]:
        query = name.strip()
        return [
            row
            for row in _FIXTURE_SCHOOLS
            if query and query in row["SCHUL_NM"]
        ]

    async def get_school(
        self, *, office_code: str, school_code: str
    ) -> list[dict[str, Any]]:
        return [
            row
            for row in _FIXTURE_SCHOOLS
            if row["ATPT_OFCDC_SC_CODE"] == office_code
            and row["SD_SCHUL_CODE"] == school_code
        ]

    async def get_lunches(
        self,
        *,
        office_code: str,
        school_code: str,
        from_ymd: str,
        to_ymd: str,
    ) -> list[dict[str, Any]]:
        start = datetime.strptime(from_ymd, "%Y%m%d").date()
        end = datetime.strptime(to_ymd, "%Y%m%d").date()

        rows: list[dict[str, Any]] = []
        cursor = start
        while cursor <= end:
            # 조회 범위의 마지막 날은 의도적으로 비워 두어 "급식 정보 없음"
            # 빈 상태 카드도 결정적으로 검증할 수 있게 한다.
            if cursor != end:
                rows.append(
                    {
                        "MMEAL_SC_CODE": "2",
                        "MLSV_YMD": _ymd(cursor),
                        "DDISH_NM": "<br/>".join(_FIXTURE_DISHES),
                        "ORPLC_INFO": "쌀: 국내산<br/>배추: 국내산",
                        "NTR_INFO": "탄수화물(g) : 120.5<br/>단백질(g) : 25.3",
                        "CAL_INFO": "650 Kcal",
                        "MLSV_FGR": "450",
                    }
                )
            cursor += timedelta(days=1)
        return rows
