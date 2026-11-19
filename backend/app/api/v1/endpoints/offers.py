from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Path, Query, status

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
    """Pull offer-to-stream bindings from Keitaro into the local database."""
    return await service.sync_from_keitaro()


@router.post("/sync/to-keitaro")
async def sync_offer_bindings_to_keitaro(service: FlowServiceDep) -> dict:
    """Push locally changed offer-to-stream bindings to Keitaro."""
    return await service.sync_to_keitaro()


@router.get("/local", response_model=LocalOfferListResponse)
async def get_local_offers(
    service: OfferServiceDep,
    include_deleted: bool = Query(default=False),
) -> LocalOfferListResponse:
    offers = await service.get_local_offers(include_deleted=include_deleted)
    return LocalOfferListResponse(items=offers, total=len(offers))


@router.get("")
async def get_keitaro_offers(service: OfferServiceDep):
    """Get the available offers directly from Keitaro."""
    return await service.get_keitaro_offers()


@router.post("", status_code=status.HTTP_201_CREATED, response_model=LocalOfferResponse)
async def add_offer(data: OfferCreateRequest, service: OfferServiceDep) -> LocalOfferResponse:
    return await service.add_offer(data.keitaro_id)


@router.patch("/{offer_id}/restore", response_model=OfferRestoreResponse)
async def restore_offer(
    offer_id: Annotated[UUID, Path()],
    service: OfferServiceDep,
) -> OfferRestoreResponse:
    offer = await service.restore_offer(offer_id)
    return OfferRestoreResponse(id=offer.id, deleted=offer.deleted, synced=offer.synced)


@router.delete("/{offer_id}", response_model=OfferDeleteResponse)
async def delete_offer(
    offer_id: Annotated[UUID, Path()],
    service: OfferServiceDep,
) -> OfferDeleteResponse:
    offer = await service.delete_offer(offer_id)
    return OfferDeleteResponse(id=offer.id, deleted=offer.deleted)


@router.get("/{offer_id}")
async def get_keitaro_offer(
    offer_id: Annotated[int, Path(gt=0)],
    service: OfferServiceDep,
):
    """Get one offer directly from Keitaro (legacy endpoint)."""
    return await service.get_keitaro_offer(offer_id)
