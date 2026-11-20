from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Path, Query, status

from app.models.models import Offer
from app.api.dependencies import OfferServiceDep, FlowServiceDep
from app.schemas.offer import (
    LocalOfferListResponse,
    LocalOfferResponse,
    OfferCreateRequest,
    OfferDeleteResponse,
    OfferRestoreResponse,
)

router = APIRouter(prefix="/offers", tags=["Offers"])


@router.post("/sync/from-keitaro")
async def sync_offer_bindings_from_keitaro(service: FlowServiceDep) -> dict:
    """Synchronize offer bindings from Keitaro into the local database.

    Retrieves all offer-to-stream bindings from Keitaro for tracked campaigns
    and updates the local database accordingly. Untracked offers are created as stubs.

    Returns sync statistics with errors count if any.
    """
    return await service.sync_from_keitaro()


@router.post("/sync/to-keitaro")
async def sync_offer_bindings_to_keitaro(service: FlowServiceDep) -> dict:
    """Synchronize changed offer bindings from local database to Keitaro.

    Pushes all unsynchronized offer bindings (FlowOffer entities) with pending changes
    to the corresponding campaign flows in Keitaro using a single PUT request per flow.

    Returns sync statistics with errors count if any.
    """
    return await service.sync_to_keitaro()


@router.get("/local", response_model=LocalOfferListResponse)
async def get_local_offers(
    service: OfferServiceDep,
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
async def get_keitaro_offers(service: OfferServiceDep):
    """Get all available offers directly from Keitaro API.

    Fetches the complete catalog of active offers from Keitaro and returns them as a list.
    This endpoint does not include deleted or archived offers from Keitaro unless explicitly
    supported by the upstream API.
    """
    return await service.get_keitaro_offers()


@router.post("", status_code=status.HTTP_201_CREATED, response_model=LocalOfferResponse)
async def add_offer(data: OfferCreateRequest, service: OfferServiceDep) -> LocalOfferResponse:
    """Import an existing Keitaro offer into the local database.

    Creates a new local record for a known offer identified by its numeric Keitaro ID.
    Fetches the full offer details from Keitaro first before storing locally. Does not
    create offers in Keitaro - only stores references to existing ones.

    Args:
        data: Request containing keitaro_id of the offer to import.

    Returns:
        Created local offer record with UUID and metadata.
    """
    return await service.add_offer(data.keitaro_id)


@router.patch("/{offer_id}/restore", response_model=OfferRestoreResponse)
async def restore_offer(
    offer_id: Annotated[UUID, Path()],
    service: OfferServiceDep,
) -> OfferRestoreResponse:
    """Restore a soft-deleted local offer record.

    Recovers an offer that was previously marked as deleted using soft delete.
    The underlying Keitaro offer is not modified - only the local database flag changes.

    Args:
        offer_id: UUID of the soft-deleted offer to restore.

    Returns:
        Restored offer record with deleted=False and metadata.
    """
    offer = await service.restore_offer(offer_id)
    return OfferRestoreResponse(id=offer.id, deleted=offer.deleted, synced=offer.synced)


@router.delete("/{offer_id}", response_model=OfferDeleteResponse)
async def delete_offer(
    offer_id: Annotated[UUID, Path()],
    service: OfferServiceDep,
) -> OfferDeleteResponse:
    """Soft-delete a local offer record.

    Marks the offer as deleted in the local database without removing it from storage.
    The underlying Keitaro offer is not modified - only the local reference is flagged.
    Offer bindings to streams continue working until explicitly updated.

    Args:
        offer_id: UUID of the offer to soft-delete.

    Returns:
        Deleted offer record with deleted=True flag.
    """
    offer: Offer = await service.delete_offer(offer_id)
    return OfferDeleteResponse(id=offer.id, deleted=offer.deleted)


@router.get("/{offer_id}")
async def get_keitaro_offer(
    offer_id: Annotated[int, Path(gt=0)],
    service: OfferServiceDep,
):
    """Get a single offer directly from Keitaro API (legacy endpoint).

    Fetches details for a specific offer by its numeric Keitaro ID from the upstream
    Keitaro system. Response format depends on current Keitaro API schema and may vary.

    Args:
        offer_id: Numeric ID of the offer in Keitaro.

    Returns:
        Offer data from Keitaro (format not guaranteed).
    """
    return await service.get_keitaro_offer(offer_id)
