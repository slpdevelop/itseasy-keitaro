from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    create_async_engine,
)

from app.core.config import Settings


def create_database_engine(settings: Settings) -> AsyncEngine:
    return create_async_engine(
        settings.postgres_db_url.get_secret_value(),
        echo=False,
        pool_pre_ping=True,
    )


async def close_database(engine: AsyncEngine) -> None:
    await engine.dispose()
