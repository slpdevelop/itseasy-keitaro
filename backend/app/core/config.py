"""Application configuration using Pydantic Settings.

Security Notice: All sensitive values (API tokens, passwords) must be set in .env file.
Never commit real secret values to version control. Copy .env.example to .env and fill in your values.
"""

import logging
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application settings
    app_name: str = "Keitaro Campaign Manage"
    app_version: str = "0.1.0"
    env: str = "development"  # development, staging, production
    debug: bool = False

    # Logging
    log_level: str = "INFO"

    @property
    def log_level_int(self) -> int:
        """Convert log level string to logging constant."""
        return getattr(logging, self.log_level.upper(), logging.INFO)


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings: Settings = get_settings()
