from __future__ import annotations

import pytest
from pydantic import ValidationError

from incident_precedent_harness.config.settings import Settings


def test_settings_default_to_local_sie_without_a_key() -> None:
    settings = Settings(_env_file=None)

    assert settings.sie_base_url == "http://localhost:8080"
    assert settings.sie_api_key is None
    assert settings.is_local_sie is True


def test_settings_reject_invalid_sie_url() -> None:
    with pytest.raises(ValidationError, match="absolute http\\(s\\) URL"):
        Settings(_env_file=None, sie_base_url="localhost:8080")
