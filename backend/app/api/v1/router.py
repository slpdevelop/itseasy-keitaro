"""API v1 router."""

from fastapi import APIRouter
from app.api.v1.endpoints import campaigns, offers

router = APIRouter(prefix="/v1", tags=["v1"])
router.include_router(campaigns.router)
router.include_router(offers.router)
