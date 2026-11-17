import logging
from functools import lru_cache
from pathlib import Path
from typing import Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.core.exceptions import ConfigurationError

# Project paths
PROJECT_ROOT = Path(__file__).resolve().parents[3]
ENV_FILE_PATH = PROJECT_ROOT / "backend" / ".env"


class Settings(BaseSettings):
    """Application configuration."""

    model_config = SettingsConfigDict(
        env_file=ENV_FILE_PATH,
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_name: str = Field(min_length=1)
    app_version: str = "0.1.0"
    env: str = "development"
    debug: bool = False

    # Keitaro
    keitaro_base_url: Optional[str] = None
    keitaro_api_token: Optional[str] = None

    # PostgreSQL
    use_postgresql: bool = False
    postgres_host: Optional[str] = None
    postgres_port: Optional[int] = None
    postgres_database: Optional[str] = None
    postgres_user: Optional[str] = None
    postgres_password: Optional[str] = None

    # Logging
    log_level: str = "INFO"

    @field_validator("env")
    @classmethod
    def validate_env(cls, value: str) -> str:
        allowed = {"development", "staging", "production"}

        value = value.lower()

        if value not in allowed:
            raise ValueError(f"ENV must be one of: {', '.join(sorted(allowed))}")

        return value

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, value: str) -> str:
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

        if settings.use_postgresql and not settings.postgres_password:
            errors.append("POSTGRES_PASSWORD is required when PostgreSQL is enabled")

    if settings.keitaro_base_url:
        if not settings.keitaro_base_url.startswith(("http://", "https://")):
            errors.append("KEITARO_BASE_URL must start with http:// or https://")

    if errors:
        raise ConfigurationError(errors)


# Application settings instance
settings: Settings = get_settings()
