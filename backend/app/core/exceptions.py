"""Application exceptions and HTTP error handlers."""

import logging
from typing import Any

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

logger: logging.Logger = logging.getLogger(__name__)


class AppError(Exception):
    """Base exception for application-specific errors.

    All business logic exceptions inherit from this class to enable centralized
    HTTP error handling. Each subclass defines status_code, error code, and
    a public message displayed to clients without exposing internal details.

    Attributes:
        status_code: HTTP status code for the error response.
        code: Unique error identifier (e.g., "CAMPAIGN_NOT_FOUND").
        public_message: User-facing error message.
    """

    status_code = 500
    code = "APPLICATION_ERROR"
    public_message = "Application error"

    def __init__(self, message: str | None = None) -> None:
        super().__init__(message or self.public_message)
        self.message: str = message or self.public_message


class InvalidRequestError(AppError):
    """Raised when request payload cannot be processed for upstream API.

    Indicates business logic validation failures (e.g., name too long,
    invalid country code) that are separate from Pydantic field validation.
    Returns 422 status with user-friendly error message.

    Attributes:
        status_code: Set to 422 for client-side request errors.
    """

    status_code = 422
    code = "INVALID_REQUEST"
    public_message = "Request data is invalid"


class OperationInProgressError(AppError):
    """An identical idempotent operation is currently being executed."""

    status_code = 409
    code = "OPERATION_IN_PROGRESS"
    public_message = "An identical campaign creation request is already in progress"


class KeitaroError(AppError):
    """Raised when Keitaro API fails or returns unexpected response.

    Wraps HTTP errors (non-2xx responses), timeouts, network failures,
    and JSON decode errors from upstream Keitaro system. Includes specific
    cause in error logs for debugging.

    Attributes:
        status_code: 502 (bad gateway) for upstream failures.
    """

    status_code = 502
    code = "KEITARO_ERROR"
    public_message = "Keitaro API request failed"


class KeitaroClientError(KeitaroError):
    """Non-404 upstream 4xx response; status is retained for diagnostics."""

    def __init__(self, upstream_status: int) -> None:
        super().__init__()
        self.upstream_status = upstream_status


class KeitaroNotFoundError(KeitaroError):
    """Raised when Keitaro answers 404 for the requested resource.

    Callers that know what was requested translate it into a precise 404
    (for example CampaignNotFoundError); otherwise it stays a 502.
    """

    code = "KEITARO_NOT_FOUND"
    public_message = "Resource not found in Keitaro"


class KeitaroTimeoutError(KeitaroError):
    """Raised when Keitaro API request exceeds configured timeout.

    Indicates slow network or overloaded Keitaro server preventing
    response within specified time window (default: 30 seconds).

    Attributes:
        status_code: 504 (gateway timeout) for upstream timeouts.
    """

    status_code = 504
    code = "KEITARO_TIMEOUT"
    public_message = "Keitaro API request timed out"


class CampaignCreationError(AppError):
    """Raised when campaign creation fails mid-process.

    Indicates multi-step campaign setup failed (Keitaro creation, flow
    creation, or database save). May require manual cleanup of partial
    data or checkpoint-based retry.

    Attributes:
        status_code: 502 for upstream orchestration failures.
    """

    status_code = 502
    code = "CAMPAIGN_CREATION_FAILED"
    public_message = "Campaign creation failed and cleanup may be required"


class CampaignNotFoundError(AppError):
    """Raised when campaign with given Keitaro ID does not exist.

    Occurs when fetching campaign details or performing operations on
    a non-existent campaign referenced by its numeric Keitaro ID.
    """

    status_code = 404
    code = "CAMPAIGN_NOT_FOUND"
    public_message = "Campaign not found"


async def app_exception_handler(request: Request, exc: AppError) -> JSONResponse:
    """Handler for all AppError subclasses.

    Client errors (4xx) are expected: they are logged as warnings and the specific
    message is returned, so the client knows what to fix. Server and upstream errors
    (5xx) are logged with a traceback and only the generic public message is returned.

    Args:
        request: Current request.
        exc: Application exception instance to handle.

    Returns:
        JSONResponse with the error code and message.
    """
    if exc.status_code >= 500:
        logger.error("Application error %s: %s", exc.code, exc, exc_info=True)
        message = exc.public_message
    else:
        logger.warning("Application error %s on %s: %s", exc.code, request.url.path, exc)
        message = exc.message
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": exc.code, "message": message}},
    )


async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    """Centralized handler for Starlette/FastAPI HTTP exceptions.

    Logs warnings for client errors (4xx) and errors for server errors (5xx).
    Returns standardized error response preserving original headers if set.
    Handles 204 No Content gracefully by returning empty payload.

    Args:
        request: FastAPI request object containing path info.
        exc: Starlette HTTP exception with status_code and detail.

    Returns:
        JSONResponse with HTTP status and formatted error message.
    """
    level = logging.ERROR if exc.status_code >= 500 else logging.WARNING
    logger.log(level, "HTTP %s on %s: %s", exc.status_code, request.url.path, exc.detail)
    message = exc.detail if isinstance(exc.detail, str) else "Request failed"
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": f"HTTP_{exc.status_code}", "message": message}},
        headers=exc.headers,
    )


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Centralized handler for Pydantic model validation errors.

    Extracts error details without exposing submitted user data (secrets).
    Returns structured validation error with location, message, and type
    for client-side form correction guidance.

    Args:
        request: FastAPI request object containing path info.
        exc: RequestValidationError with parsed Pydantic errors.

    Returns:
        JSONResponse with status 422 and validation details list.
    """
    # Do not expose submitted values or Pydantic context (which may contain secrets).
    details: list[dict[str, Any]] = [
        {
            "loc": list(error.get("loc", ())),
            "msg": error.get("msg", "Invalid value"),
            "type": error.get("type", "value_error"),
        }
        for error in exc.errors()
    ]
    logger.warning("Request validation failed on %s: %s", request.url.path, details)
    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Request validation failed",
                "details": details,
            }
        },
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Catch-all handler for unexpected exceptions not caught elsewhere.

    Logs full traceback with exception type and message. Returns generic
    internal server error response to prevent leaking stack traces or
    debugging information to clients. Should rarely be triggered in production.

    Args:
        request: FastAPI request object containing path info.
        exc: Uncaught Exception instance that bypassed all handlers.

    Returns:
        JSONResponse with status 500 and generic error message.
    """
    logger.error(
        "Unhandled exception on %s: %s", request.url.path, type(exc).__name__, exc_info=True
    )
    return JSONResponse(
        status_code=500,
        content={"error": {"code": "INTERNAL_SERVER_ERROR", "message": "Internal server error"}},
    )


class FlowNotFoundError(AppError):
    """Raised when a local flow UUID does not exist."""

    status_code = 404
    code = "FLOW_NOT_FOUND"
    public_message = "Flow not found"
