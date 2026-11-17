"""API v1 router."""

from fastapi import APIRouter

from app.api.v1.endpoints import health

# Create main router with prefix
main_router = APIRouter()
main_router.include_router(health.router)


# Create versioned router
router = APIRouter(prefix="/v1", tags=["v1"])
router.include_router(main_router)
