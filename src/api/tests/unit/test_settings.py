"""`Settings`의 fixture 모드/`NEIS_API_KEY` 검증 단위 테스트."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from bsl_api.settings import Settings


def test_settings_requires_api_key_without_fixture_mode() -> None:
    with pytest.raises(ValidationError, match="NEIS_API_KEY"):
        Settings(neis_api_key=None, neis_fixture_mode=False)


def test_settings_allows_missing_api_key_in_fixture_mode() -> None:
    settings = Settings(neis_api_key=None, neis_fixture_mode=True)

    assert settings.neis_fixture_mode is True
    assert settings.neis_api_key is None


def test_settings_accepts_api_key_when_provided() -> None:
    settings = Settings(neis_api_key="test-key", neis_fixture_mode=False)

    assert settings.neis_api_key == "test-key"
