"""API v1 router."""

from fastapi import APIRouter

# Create versioned router
router = APIRouter(prefix="/v1", tags=["v1"])
