from typing import Annotated

from uuid import UUID

from app.api.dependencies import CampaignServiceDep
from app.schemas.campaign import (
    CampaignDetailResponse,
    KTCampaignCreateRequest,
    KTCampaignCreateResponse,
    SyncResult,
)
from app.schemas.flow import FlowOffersUpdateRequest
from fastapi import APIRouter, Path, status

router = APIRouter(prefix="/campaigns", tags=["Campaigns"])


@router.get("")
async def get_campaigns(service: CampaignServiceDep) -> list[dict]:
    """Retrieve a filtered list of campaigns from Keitaro."""
    return await service.get_campaigns()


@router.get("/{campaign_id}", response_model=CampaignDetailResponse)
async def get_campaign_detail(
    campaign_id: Annotated[int, Path(gt=0)], service: CampaignServiceDep
) -> CampaignDetailResponse:
    """Retrieve detailed information about a specific campaign."""
    return await service.get_campaign_detail(campaign_id)


@router.post("", status_code=status.HTTP_201_CREATED, response_model=KTCampaignCreateResponse)
async def create_campaign(
    data: KTCampaignCreateRequest, service: CampaignServiceDep
) -> KTCampaignCreateResponse:
    """Create a new campaign with associated GEO and OFFER flows."""
    return await service.create_campaign(data)


@router.post("/{campaign_id}/sync", response_model=SyncResult)
async def sync_campaign(
    campaign_id: Annotated[int, Path(gt=0)], service: CampaignServiceDep
) -> SyncResult:
    """Push pending local offer changes of one campaign's flows to Keitaro.

    Only OFFER flows of the given campaign (Keitaro ID) with unsynchronized
    bindings are sent. A failure on one flow does not stop the others; it is
    reported in the result with the stage it happened at.
    """
    return await service.sync_campaign(campaign_id)


@router.post("/{campaign_id}/fetch", response_model=CampaignDetailResponse)
async def fetch_campaign(
    campaign_id: Annotated[int, Path(gt=0)], service: CampaignServiceDep
) -> CampaignDetailResponse:

    return await service.fetch_campaign(campaign_id)


@router.put("/streams/{flow_id}")
async def update_campaign_stream_offers(
    flow_id: UUID,
    data: FlowOffersUpdateRequest,
    service: CampaignServiceDep,
) -> dict:
    """Update local offer bindings for a campaign stream.

    The operation only changes local state. Use POST /offers/sync/to-keitaro
    to push pending changes to Keitaro.
    """
    return await service.update_flow_offers(
        flow_id,
        [item.model_dump() for item in data.offers],
    )
