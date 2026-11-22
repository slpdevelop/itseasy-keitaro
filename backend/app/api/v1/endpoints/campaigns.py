from typing import Annotated

from uuid import UUID

from app.api.dependencies import ServiceDep
from app.schemas.campaign import (
    CampaignDetailResponse,
    KTCampaignCreateRequest,
    KTCampaignCreateResponse,
    SyncResult,
    RemoteCampaignSummary,
)
from app.schemas.flow import FlowOffersUpdateRequest, FlowOffersUpdateResponse
from fastapi import APIRouter, Path, Response, status

router = APIRouter(prefix="/campaigns", tags=["Campaigns"])


@router.get("", response_model=list[RemoteCampaignSummary])
async def get_campaigns(service: ServiceDep) -> list[RemoteCampaignSummary]:
    """Retrieve a filtered list of campaigns from Keitaro."""
    return await service.get_campaigns()


@router.post("", status_code=status.HTTP_201_CREATED, response_model=KTCampaignCreateResponse)
async def create_campaign(
    data: KTCampaignCreateRequest, service: ServiceDep
) -> KTCampaignCreateResponse:
    """Create a new campaign with associated GEO and OFFER flows."""
    return await service.create_campaign(data)


@router.post("/{campaign_id}/sync", response_model=SyncResult)
async def sync_campaign(
    campaign_id: Annotated[int, Path(gt=0)], service: ServiceDep, response: Response
) -> SyncResult:
    """Push pending local offer changes of one campaign's flows to Keitaro.

    Only OFFER flows of the given campaign (Keitaro ID) with unsynchronized
    bindings are sent. A failure on one flow does not stop the others; it is
    reported in the result with the stage it happened at.
    """
    result = await service.sync_campaign(campaign_id)
    if result.errors:
        response.status_code = 207
    return result


@router.post("/{campaign_id}/fetch", response_model=CampaignDetailResponse)
async def fetch_campaign(
    campaign_id: Annotated[int, Path(gt=0)], service: ServiceDep
) -> CampaignDetailResponse:
    """Pull a campaign with its flows and offers from Keitaro into the local database."""
    return await service.fetch_campaign(campaign_id)


@router.put("/streams/{flow_id}", response_model=FlowOffersUpdateResponse)
async def update_campaign_stream_offers(
    flow_id: UUID,
    data: FlowOffersUpdateRequest,
    service: ServiceDep,
) -> FlowOffersUpdateResponse:
    """Update local offer bindings for a campaign stream.

    The operation only changes local state. Use POST /campaigns/{campaign_id}/sync
    to push pending changes to Keitaro.
    """
    return await service.update_flow_offers(flow_id, data)
