"""PostgreSQL connection lifecycle used by the application lifespan."""

import asyncio
import logging
import re
from urllib.parse import quote_plus

from pydantic import SecretStr
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from app.core.config import Settings
from app.core.exceptions import DatabaseConnectionError

logger = logging.getLogger(__name__)

# The database container may still be starting when the application boots, so
# connectivity checks are retried. Only idempotent operations run here:
# SELECT 1 and CREATE DATABASE when the database is missing.
CONNECT_ATTEMPTS = 5
CONNECT_RETRY_DELAY_SECONDS = 1.0
CONNECT_TIMEOUT_SECONDS = 10.0

# The database name is interpolated into CREATE DATABASE, so restrict its charset.
_DATABASE_NAME_RE = re.compile(r"^[A-Za-z0-9_]+$")


def _secret_text(value: SecretStr | str | None) -> str:
    if value is None:
        return ""
    return value.get_secret_value() if isinstance(value, SecretStr) else value


def _required(value: str, field: str) -> str:
    if not value:
        raise DatabaseConnectionError(f"{field} must be set when PostgreSQL is enabled")
    return value


def _target_database(settings: Settings) -> str:
    return _required(_secret_text(settings.postgres_database), "POSTGRES_DATABASE")


def build_database_url(settings: Settings, *, database: str | None = None) -> str:
    """Build the async SQLAlchemy URL.

    The result contains the database password and must never be logged.
    """
    host = _required(settings.postgres_host or "", "POSTGRES_HOST")
    if settings.postgres_port is None:
        raise DatabaseConnectionError("POSTGRES_PORT must be set when PostgreSQL is enabled")
    user = _required(_secret_text(settings.postgres_user), "POSTGRES_USER")
    password = _required(_secret_text(settings.postgres_password), "POSTGRES_PASSWORD")
    target = _required(database, "POSTGRES_DATABASE") if database is not None else _target_database(settings)
    return f"postgresql+asyncpg://{quote_plus(user)}:{quote_plus(password)}@{host}:{settings.postgres_port}/{quote_plus(target)}"


def _safe_message(settings: Settings, exc: Exception) -> str:
    """Exception text with the password masked so it is safe to log."""
    message = f"{type(exc).__name__}: {exc}"
    password = _secret_text(settings.postgres_password)
    if password:
        message = message.replace(password, "***")
    return message


async def ensure_database_exists(settings: Settings) -> None:
    """Create the target database when it does not exist yet (idempotent)."""
    database = _target_database(settings)
    if not _DATABASE_NAME_RE.fullmatch(database):
        raise DatabaseConnectionError(
            "POSTGRES_DATABASE must contain only letters, digits and underscores because it is used to create the database"
        )
    admin_engine = create_async_engine(
        build_database_url(settings, database="postgres"),
        isolation_level="AUTOCOMMIT",
        connect_args={"timeout": CONNECT_TIMEOUT_SECONDS},
    )
    try:
        async with admin_engine.connect() as connection:
            result = await connection.execute(
                text("SELECT 1 FROM pg_database WHERE datname = :name"),
                {"name": database},
            )
            if result.scalar() is None:
                await connection.execute(text(f'CREATE DATABASE "{database}"'))
                logger.info("PostgreSQL database %s created", database)
    finally:
        await admin_engine.dispose()


async def connect_database(settings: Settings) -> AsyncEngine:
    """Create the application engine and verify connectivity, retrying while the container starts."""
    url = build_database_url(settings)
    last_error: DatabaseConnectionError | None = None

    for attempt in range(1, CONNECT_ATTEMPTS + 1):
        engine: AsyncEngine | None = None
        try:
            await ensure_database_exists(settings)
            engine = create_async_engine(
                url,
                pool_pre_ping=True,
                connect_args={"timeout": CONNECT_TIMEOUT_SECONDS},
            )
            async with engine.connect() as connection:
                await connection.execute(text("SELECT 1"))
            logger.info("PostgreSQL connection established (database=%s)", _target_database(settings))
            return engine
        except DatabaseConnectionError:
            raise
        except Exception as exc:
            # Any failure here is re-raised as a sanitized startup error after the retries.
            if engine is not None:
                await engine.dispose()
            last_error = DatabaseConnectionError(
                f"PostgreSQL connection attempt {attempt}/{CONNECT_ATTEMPTS} failed: {_safe_message(settings, exc)}"
            )
            logger.warning("%s", last_error.message)
            if attempt < CONNECT_ATTEMPTS:
                await asyncio.sleep(CONNECT_RETRY_DELAY_SECONDS)

    if last_error is None:
        last_error = DatabaseConnectionError("PostgreSQL connection failed")
    raise last_error


async def disconnect_database(engine: AsyncEngine) -> None:
    """Close the application engine and release all pooled connections."""
    await engine.dispose()
