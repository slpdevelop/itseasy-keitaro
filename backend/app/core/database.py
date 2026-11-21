from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    create_async_engine,
)

from app.core.config import Settings


def create_database_engine(settings: Settings) -> AsyncEngine:
    """Create an async SQLAlchemy engine from application settings.

    Uses the PostgreSQL DSN from Settings with connection pooling pre-ping
    enabled for healthy connection validation before checkout.

    Args:
        settings: Application settings containing the database URL.

    Returns:
        Configured AsyncEngine instance.
    """
    return create_async_engine(
        settings.postgres_db_url.get_secret_value(),
        echo=False,
        pool_pre_ping=True,
    )


async def close_database(engine: AsyncEngine) -> None:
    """Dispose of the database engine and close all pooled connections.

    Should be called during application shutdown to release resources.

    Args:
        engine: AsyncEngine instance to dispose.
    """
    await engine.dispose()
