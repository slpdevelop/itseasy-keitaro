from typing import Annotated

from app.api.dependencies import CampaignServiceDep
from app.schemas.campaign import (
    CampaignDetailResponse,
    KTCampaignCreateRequest,
    KTCampaignCreateResponse,
)
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
