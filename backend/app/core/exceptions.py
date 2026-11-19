"""Application exceptions and HTTP error handlers."""

import logging
from typing import Any

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)


class AppError(Exception):
    """Base exception for application-specific errors."""

    status_code = 500
    code = "APPLICATION_ERROR"
    public_message = "Application error"

    def __init__(self, message: str | None = None) -> None:
        super().__init__(message or self.public_message)
        self.message = message or self.public_message


class ConfigurationError(AppError):
    """Raised when application configuration is invalid."""

    code = "CONFIGURATION_ERROR"
    public_message = "Application configuration error"

    def __init__(self, errors: list[str] | None = None, message: str | None = None) -> None:
        self.errors = errors or []
        super().__init__(message or "; ".join(self.errors) or self.public_message)


class DatabaseConnectionError(AppError):
    """PostgreSQL could not be created or reached during startup."""

    code = "DATABASE_CONNECTION_ERROR"
    public_message = "Database connection failed"


class InvalidRequestError(AppError):
    """Raised when valid request fields cannot be represented for the upstream API."""

    status_code = 422
    code = "INVALID_REQUEST"
    public_message = "Request data is invalid"


class KeitaroError(AppError):
    """Keitaro returned an invalid response or could not be reached."""

    status_code = 502
    code = "KEITARO_ERROR"
    public_message = "Keitaro API request failed"


class KeitaroTimeoutError(KeitaroError):
    status_code = 504
    code = "KEITARO_TIMEOUT"
    public_message = "Keitaro API request timed out"


class CampaignCreationError(AppError):
    status_code = 502
    code = "CAMPAIGN_CREATION_FAILED"
    public_message = "Campaign creation failed and cleanup may be required"

class CampaignNotFoundError(AppError):
    status_code = 404
    code = "CAMPAIGN_NOT_FOUND"
    public_message = "Campaign not found"


async def app_exception_handler(request: Request, exc: AppError) -> JSONResponse:
    logger.error("Application error %s: %s", exc.code, exc, exc_info=True)
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": exc.code, "message": exc.public_message}},
    )


async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    level = logging.ERROR if exc.status_code >= 500 else logging.WARNING
    logger.log(level, "HTTP %s on %s: %s", exc.status_code, request.url.path, exc.detail)
    message = exc.detail if isinstance(exc.detail, str) else "Request failed"
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": f"HTTP_{exc.status_code}", "message": message}},
        headers=exc.headers,
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    # Do not expose submitted values or Pydantic context (which may contain secrets).
    details: list[dict[str, Any]] = [
        {"loc": list(error.get("loc", ())), "msg": error.get("msg", "Invalid value"), "type": error.get("type", "value_error")}
        for error in exc.errors()
    ]
    logger.warning("Request validation failed on %s: %s", request.url.path, details)
    return JSONResponse(
        status_code=422,
        content={"error": {"code": "VALIDATION_ERROR", "message": "Request validation failed", "details": details}},
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.error("Unhandled exception on %s: %s", request.url.path, type(exc).__name__, exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"error": {"code": "INTERNAL_SERVER_ERROR", "message": "Internal server error"}},
    )
