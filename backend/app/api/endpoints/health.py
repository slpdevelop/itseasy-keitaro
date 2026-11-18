"""Health check endpoint."""

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class HealthResponse(BaseModel):
    """Health check response model."""

    status: str = "ok"
    message: str = "OK"


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Check application health",
    description="Returns health status of the application.",
    responses={
        "200": {"description": "Application is healthy"},
    },
)
async def health_check() -> HealthResponse:
    """Perform health check."""
    return HealthResponse(status="ok", message="OK")
