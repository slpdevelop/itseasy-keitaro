"""FastAPI application entry point."""

import logging
from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

from fastapi import APIRouter, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.config import Config

from app.core.config import settings
from app.core.exceptions import exception_handler

from app.api.v1.router import router as v1_router

# Configure logging at application startup
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifecycle events."""
    # Startup
    logger.info("Starting Keitaro Campaign Manager...")
    logger.debug(f"   Environment: {settings.env}")
    logger.debug(f"   Debug mode: {settings.debug}")

    yield

    # Shutdown
    logger.info("Shutting down Keitaro Campaign Manager...")


def get_app() -> FastAPI:
    """Create and configure FastAPI application."""
    application = FastAPI(
        title="Keitaro Campaign Manager",
        description="Campaign manager for Keitaro advertising tracker via API",
        version="0.1.0",
        docs_url="/docs" if settings.env == "development" else None,
        redoc_url=None,
        openapi_url="/openapi.json" if settings.env == "development" else None,
        lifespan=lifespan,
    )

    # Create API router with version prefix
    api_router = APIRouter(prefix="/api", tags=["API"])

    api_router.include_router(v1_router)
    application.include_router(api_router)

    # Add CORS middleware
    # Only allow requests from known origins in development
    application.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:5173",  # Vite dev server default
            "http://127.0.0.1:5173",
            "http://localhost:3000",  # Alternative dev server port
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register exception handlers
    application.add_exception_handler(Exception, exception_handler)

    return application


app: FastAPI = get_app()
