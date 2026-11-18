"""FastAPI application entry point."""

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware


from app.core.exceptions import (
    http_exception_handler,
    unhandled_exception_handler,
    validation_exception_handler,
)
from app.core.config import Settings, get_settings


from app.api.v1.router import router as v1_router
from app.api.endpoints.health import router as health_router

logger: logging.Logger = logging.getLogger(__name__)


def setup_logging(settings: Settings) -> None:
    # Configure logging at application startup
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncGenerator[None]:
    """Application lifecycle events."""
    settings: Settings = app.state.settings

    # Startup
    logger.info("Starting Keitaro Campaign Manager...")
    logger.debug("   Environment:  %s", settings.env)
    logger.debug("   Debug mode: %s", settings.debug)

    yield

    # Shutdown
    logger.info("Shutting down Keitaro Campaign Manager...")


def get_app(settings: Optional[Settings] = None) -> FastAPI:
    """Create and configure FastAPI application."""
    if settings is None:
        settings: Settings = get_settings()
    setup_logging(settings)

    application = FastAPI(
        title=settings.app_name,
        description=settings.app_description,
        version=settings.app_version,
        docs_url="/docs" if settings.env == "development" else None,
        redoc_url=None,
        openapi_url="/openapi.json" if settings.env == "development" else None,
        lifespan=lifespan,
    )

    application.state.settings = settings
    application.dependency_overrides[get_settings] = lambda: settings

    application.include_router(v1_router, prefix="/api")
    application.include_router(health_router)

    # Add CORS middleware
    # Only allow requests from known origins in development
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_hosts,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register exception handlers
    application.add_exception_handler(
        HTTPException,
        http_exception_handler,
    )

    application.add_exception_handler(
        RequestValidationError,
        validation_exception_handler,
    )

    application.add_exception_handler(
        Exception,
        unhandled_exception_handler,
    )

    return application


app: FastAPI = get_app()
