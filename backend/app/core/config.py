"""Application configuration using Pydantic Settings."""

import logging
from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import AliasChoices, Field, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.core.exceptions import ConfigurationError

PROJECT_ROOT = Path(__file__).resolve().parents[2]
ENV_FILE_PATH = PROJECT_ROOT / ".env"


def _is_configured(value: object) -> bool:
    """Treat missing and blank values (including empty secrets) as not configured."""
    if isinstance(value, SecretStr):
        return bool(value.get_secret_value())
    if isinstance(value, str):
        return bool(value.strip())
    return value is not None


class Settings(BaseSettings):
    """Application configuration."""

    model_config = SettingsConfigDict(
        env_file=ENV_FILE_PATH,
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        populate_by_name=True,
    )

    # Application
    app_name: str = "Keitaro Campaign Manager"
    app_version: str = "0.1.0"
    app_description: str = "Campaign manager for Keitaro advertising tracker via API"
    env: Literal["development", "staging", "production"] = "development"
    debug: bool = False

    # Keitaro
    keitaro_base_url: str = Field(min_length=1)
    keitaro_api_token: SecretStr = Field(min_length=1)
    keitaro_timeout_seconds: int = Field(default=30, ge=1)

    # Campaign defaults
    campaign_name_prefix: str = "test_zhestkov_"
    campaign_group_id: int = Field(default=10332, gt=0)
    campaign_domain_id: int = Field(default=1813, gt=0)
    campaign_traffic_source_id: int = Field(default=836, gt=0)

    # Optional local storage configuration. Not used unless PostgreSQL support is enabled.
    use_postgresql: bool = False
    postgres_host: str | None = None
    postgres_port: int | None = Field(default=None, ge=1, le=65535)
    postgres_database: SecretStr | None = None
    postgres_user: SecretStr | None = None
    postgres_password: SecretStr | None = None

    # CORS
    cors_allowed_origins: list[str] = Field(
        default_factory=list,
        validation_alias=AliasChoices("CORS_ALLOWED_ORIGINS", "ALLOWED_HOSTS"),
    )
    cors_allow_credentials: bool = False

    # Logging
    log_level: str = "INFO"

    @field_validator("env", mode="before")
    @classmethod
    def normalize_env(cls, value: str) -> str:
        return value.lower() if isinstance(value, str) else value

    @field_validator("keitaro_base_url")
    @classmethod
    def validate_keitaro_base_url(cls, value: str) -> str:
        value = value.rstrip("/")
        if not value.startswith(("http://", "https://")):
            raise ValueError("KEITARO_BASE_URL must start with http:// or https://")
        return value

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, value: str) -> str:
        value = value.upper()
        if not isinstance(getattr(logging, value, None), int):
            raise ValueError(f"Invalid LOG_LEVEL: {value}")
        return value

    @field_validator("campaign_name_prefix")
    @classmethod
    def validate_campaign_name_prefix(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("CAMPAIGN_NAME_PREFIX cannot be blank")
        return value.strip()

    @model_validator(mode="after")
    def validate_cors_and_postgres(self) -> "Settings":
        if self.cors_allow_credentials and "*" in self.cors_allowed_origins:
            raise ValueError("CORS wildcard origin cannot be used with credentials")
        if self.use_postgresql:
            missing = [
                name
                for name, value in (
                    ("POSTGRES_HOST", self.postgres_host),
                    ("POSTGRES_PORT", self.postgres_port),
                    ("POSTGRES_DATABASE", self.postgres_database),
                    ("POSTGRES_USER", self.postgres_user),
                    ("POSTGRES_PASSWORD", self.postgres_password),
                )
                if not _is_configured(value)
            ]
            if missing:
                raise ValueError(f"PostgreSQL is enabled but settings are missing or empty: {', '.join(missing)}")
        return self

    @property
    def log_level_int(self) -> int:
        return getattr(logging, self.log_level)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    settings = Settings()
    validate_settings(settings)
    return settings


def validate_settings(settings: Settings) -> None:
    """Keep application-level validation separate from Pydantic field parsing."""
    errors: list[str] = []
    if settings.env == "production" and not settings.keitaro_api_token.get_secret_value():
        errors.append("KEITARO_API_TOKEN is required in production")
    if errors:
        raise ConfigurationError(errors)
