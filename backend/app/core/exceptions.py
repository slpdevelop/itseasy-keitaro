"""Application exceptions and HTTP error handlers."""

import logging

from fastapi import HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)


class AppError(Exception):
    """Base exception for application-specific errors."""


class ConfigurationError(AppError):
    """Raised when application configuration is invalid or missing required values."""

    def __init__(
        self,
        errors: list[str] | None = None,
        message: str | None = None,
    ) -> None:
        self.errors = errors or []
        super().__init__(message or "; ".join(self.errors))


async def http_exception_handler(
    request: Request,
    exc: HTTPException,
) -> JSONResponse:
    """Handle HTTP exceptions."""

    logger.warning("HTTP %s: %s", exc.status_code, exc.detail)

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": f"HTTP_{exc.status_code}",
                "message": str(exc.detail),
            }
        },
        headers=exc.headers,
    )


async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    """Handle request validation errors."""

    logger.warning("Request validation failed: %s", exc)

    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Request validation failed",
            }
        },
    )


async def unhandled_exception_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    """Handle unexpected application exceptions."""

    logger.error(
        "Unhandled exception: %s: %s",
        type(exc).__name__,
        exc,
        exc_info=True,
    )

    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "Internal server error",
            }
        },
    )
