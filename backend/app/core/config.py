"""Application configuration using Pydantic Settings."""

import logging
from functools import lru_cache
from pathlib import Path

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.core.exceptions import ConfigurationError

# Project paths
PROJECT_ROOT: Path = Path(__file__).resolve().parents[2]  # backend root
ENV_FILE_PATH: Path = PROJECT_ROOT / ".env"


class Settings(BaseSettings):
    """Application configuration."""

    model_config = SettingsConfigDict(
        env_file=ENV_FILE_PATH,
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_name: str = "Keitaro Campaign Manager"
    app_version: str = "0.1.0"
    app_description: str = "Campaign manager for Keitaro advertising tracker via API"
    env: str
    debug: bool

    # Keitaro
    keitaro_base_url: str
    keitaro_api_token: SecretStr
    keitaro_timeout_seconds: int

    # PostgreSQL (optional - for local data storage)
    use_postgresql: bool
    postgres_host: str = Field(default="localhost", min_length=1)
    postgres_port: int = Field(ge=1, le=65535)
    postgres_database: SecretStr
    postgres_user: SecretStr
    postgres_password: SecretStr

    # CORS
    allowed_hosts: list[str]

    # Logging
    log_level: str = "DEBUG"

    @field_validator("env")
    @classmethod
    def validate_env(cls, value: str) -> str:
        """Validate environment variable."""
        allowed = {"development", "staging", "production"}

        value = value.lower()

        if value not in allowed:
            raise ValueError(f"ENV must be one of: {', '.join(sorted(allowed))}")

        return value

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, value: str) -> str:
        """Validate log level."""
        value = value.upper()

        if not isinstance(getattr(logging, value, None), int):
            raise ValueError(f"Invalid LOG_LEVEL: {value}")

        return value

    @property
    def log_level_int(self) -> int:
        """Return logging level as integer."""
        return getattr(logging, self.log_level)

    @property
    def keitaro_enabled(self) -> bool:
        """Check whether Keitaro integration is configured."""
        return bool(self.keitaro_base_url and self.keitaro_api_token)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return cached application settings."""
    settings = Settings()
    validate_settings(settings)
    return settings


def validate_settings(settings: Settings) -> None:
    """Validate application configuration."""

    errors = []

    if settings.env == "production":
        if not settings.keitaro_base_url:
            errors.append("KEITARO_BASE_URL is required in production")

        if not settings.keitaro_api_token:
            errors.append("KEITARO_API_TOKEN is required in production")

    if settings.keitaro_base_url:
        if not settings.keitaro_base_url.startswith(("http://", "https://")):
            errors.append("KEITARO_BASE_URL must start with http:// or https://")

    if errors:
        raise ConfigurationError(errors)
