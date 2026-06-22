"""Settings for local-first inference operation.

Secrets are represented as SecretStr and are intentionally never serialized by this module.
"""

from __future__ import annotations

from functools import lru_cache
from urllib.parse import urlparse

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Environment-backed application settings.

    The initial supported provider mode is local Docker SIE. A non-local URL remains
    a future compatibility seam and does not establish hosted-provider access.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    sie_base_url: str = Field(default="http://localhost:8080")
    sie_api_key: SecretStr | None = Field(default=None)
    sie_timeout_seconds: float = Field(default=30.0, gt=0, le=120)

    @field_validator("sie_base_url")
    @classmethod
    def validate_sie_base_url(cls, value: str) -> str:
        normalized = value.rstrip("/")
        parsed = urlparse(normalized)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise ValueError("sie_base_url must be an absolute http(s) URL")
        return normalized

    @property
    def is_local_sie(self) -> bool:
        """Return whether the configured endpoint is a local-machine endpoint."""
        hostname = urlparse(self.sie_base_url).hostname
        return hostname in {"localhost", "127.0.0.1", "::1"}


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Load and cache settings for the active process."""
    return Settings()
