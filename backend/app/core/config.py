"""Application configuration using Pydantic Settings."""

import logging
from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import (
    AliasChoices,
    Field,
    SecretStr,
    field_validator,
)
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT: Path = Path(__file__).resolve().parents[2]
ENV_FILE_PATH: Path = PROJECT_ROOT / ".env"


class Settings(BaseSettings):
    """Application configuration loaded from environment variables.

    All settings are read from `.env` file with UTF-8 encoding. Case-insensitive
    matching allows variations like `POSTGRES_HOST` and `postgres_host`. Extra
    unknown fields are ignored for backward compatibility. Name-population enables
    accessing fields by both alias and name.

    Sensitive values like passwords are stored as SecretStr and never logged.
    Missing or invalid values fail fast at startup with a pydantic ValidationError.

    **Required environment variables:**
        - `KEITARO_BASE_URL`: Keitaro admin API base URL (http(s)://)
        - `KEITARO_API_TOKEN`: Authentication token for Keitaro API
        - `POSTGRES_DB_URL`: SQLAlchemy async DSN, e.g. postgresql+asyncpg://user:pass@host/db

    **Configuration defaults:**
        - Development environment with debug mode off
        - Campaign name prefix: "test_zhestkov_"
        - Group, domain, and traffic source IDs set per test environment
    """

    model_config = SettingsConfigDict(
        env_file=ENV_FILE_PATH,
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        populate_by_name=True,
    )

    # Application metadata
    app_name: str = "Keitaro Campaign Manager"
    """Application name displayed in UI and logs."""
    app_version: str = "0.1.0"
    """Current version string."""
    app_description: str = "Campaign manager for Keitaro advertising tracker via API"
    """Human-readable description of the application."""

    # Environment mode
    env: Literal["development", "staging", "production"] = "development"
    """Application environment. Affects logging, CORS, and some validations."""
    debug: bool = False
    """Enable debug mode with detailed error traces (default: False)."""

    # Keitaro API settings (required)
    keitaro_base_url: str = Field(min_length=1)
    """Keitaro admin API base URL. Must start with http:// or https://."""
    keitaro_api_token: SecretStr = Field(min_length=1)
    """API token for authenticating requests to Keitaro admin API."""
    keitaro_timeout_seconds: int = Field(default=30, ge=1)
    """HTTP request timeout in seconds for Keitaro API calls (default: 30)."""

    # Campaign creation defaults
    campaign_name_prefix: str = "test_zhestkov_"
    """Prefix added to all created campaigns. Max length: 255."""
    campaign_group_id: int = Field(default=10332, gt=0)
    """Default Keitaro group ID for new campaigns (default: 10332)."""
    campaign_domain_id: int = Field(default=1813, gt=0)
    """Default Keitaro domain ID for new campaigns (default: 1813)."""
    campaign_traffic_source_id: int = Field(default=836, gt=0)
    """Default Keitaro traffic source ID for new campaigns (default: 836)."""

    # Local PostgreSQL storage configuration
    postgres_db_url: SecretStr

    # CORS configuration
    cors_allowed_origins: list[str] = Field(
        default_factory=list,
        validation_alias=AliasChoices("CORS_ALLOWED_ORIGINS", "ALLOWED_HOSTS"),
    )
    """Allowed CORS origins. Set as a JSON list: ["http://localhost:3000"]."""
    cors_allow_credentials: bool = False
    """Allow credentials (cookies, auth headers) in cross-origin requests."""

    # Logging configuration
    log_level: str = "INFO"
    """Logging level: DEBUG, INFO, WARNING, ERROR, CRITICAL."""

    @field_validator("env", mode="before")
    @classmethod
    def normalize_env(cls, value: str) -> str:
        """Normalize environment string to lowercase for consistent handling."""
        return value.lower() if isinstance(value, str) else value

    @field_validator("keitaro_base_url")
    @classmethod
    def validate_keitaro_base_url(cls, value: str) -> str:
        """Validate Keitaro base URL format.

        Must be a valid HTTP(S) URL without trailing slash normalization issues.
        """
        value = value.rstrip("/")
        if not value.startswith(("http://", "https://")):
            raise ValueError("KEITARO_BASE_URL must start with http:// or https://")
        return value

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, value: str) -> str:
        """Validate logging level against Python's logging module constants."""
        value = value.upper()
        if not isinstance(getattr(logging, value, None), int):
            raise ValueError(f"Invalid LOG_LEVEL: {value}")
        return value

    @field_validator("campaign_name_prefix")
    @classmethod
    def validate_campaign_name_prefix(cls, value: str) -> str:
        """Ensure campaign name prefix is not blank after stripping whitespace."""
        if not value.strip():
            raise ValueError("CAMPAIGN_NAME_PREFIX cannot be blank")
        return value.strip()

    @property
    def log_level_int(self) -> int:
        """Return logging level as integer for compatibility with logging module."""
        return getattr(logging, self.log_level)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Get the cached settings instance.

    Uses lru_cache so only one Settings object exists and the configuration cannot
    change between requests.

    Returns:
        Single shared Settings instance with validated configuration.
    """
    return Settings()
