from fastapi import APIRouter, Query

from app.models.models import Offer
from app.api.dependencies import CampaignServiceDep, KeitaroAPIDep
from app.schemas.offer import (
    LocalOfferListResponse,
)

router = APIRouter(prefix="/offers", tags=["Offers"])


@router.get("/local", response_model=LocalOfferListResponse)
async def get_local_offers(
    service: CampaignServiceDep,
    include_deleted: bool = Query(default=False),
) -> LocalOfferListResponse:
    """Get locally stored offers (optional soft-deleted items).

    Retrieves all offer entities from the local database. Use `include_deleted=true`
    to also retrieve soft-deleted offers. Returns paginated list with total count.

    Args:
        include_deleted: Include soft-deleted offers in response. Default: False.

    Returns:
        List of offers with pagination metadata.
    """
    offers: list[Offer] = await service.get_local_offers(include_deleted=include_deleted)
    return LocalOfferListResponse(items=offers, total=len(offers))


@router.get("")
async def get_keitaro_offers(api: KeitaroAPIDep):
    """Get all available offers directly from Keitaro API.

    Fetches the complete catalog of active offers from Keitaro and returns them as a list.
    This endpoint does not include deleted or archived offers from Keitaro unless explicitly
    supported by the upstream API.
    """
    return await api.get_keitaro_offers()
