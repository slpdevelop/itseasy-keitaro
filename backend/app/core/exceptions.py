"""Application exceptions and error responses."""

import logging

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException


class ConfigurationError(Exception):
    """Raised when application configuration is invalid or missing required values."""

    def __init__(self, errors: list[str] | None = None, message: str | None = None):
        self.errors = errors or []
        super().__init__(message or "; ".join(self.errors))


async def exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle uncaught exceptions and return JSON response."""
    if isinstance(exc, StarletteHTTPException):
        logger = logging.getLogger(__name__)
        logger.warning(f"HTTP {exc.status_code}: {exc.detail}")

        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": exc.detail if isinstance(exc.detail, str) else str(exc.detail),
            },
        )

    # Log unexpected errors
    logger = logging.getLogger(__name__)
    logger.error(f"Unhandled exception: {type(exc).__name__}: {exc}", exc_info=True)

    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error"},
    )
