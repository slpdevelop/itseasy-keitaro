from ast import Dict

from app.interfaces.campaign_gateway import CampaignGateway
from app.schemas.campaign import CampaignCreate, KeitaroCampaignCreateRequest
from app.constants import (
    CAMPAIGN_NAME_PREFIX,
    CAMPAIGN_DOMAIN_ID,
    CAMPAIGN_GROUP_ID,
    CAMPAIGN_TRAFFIC_SOURCE_ID,
)
from fastapi import HTTPException


class CampaignService:

    def __init__(self, gateway: CampaignGateway):
        self.gateway: CampaignGateway = gateway

    async def get_campaigns(self) -> list[dict]:
        campaigns = await self.gateway.get_campaigns()

        return [
            campaign
            for campaign in campaigns
            if (campaign.get("name") or "").startswith(CAMPAIGN_NAME_PREFIX)
        ]

    async def create_campaign(
        self,
        data: KeitaroCampaignCreateRequest,
    ) -> dict:

        request_data = CampaignCreate(
            name=data.name,
            domain_id=CAMPAIGN_DOMAIN_ID,
            group_id=CAMPAIGN_GROUP_ID,
            traffic_source_id=CAMPAIGN_TRAFFIC_SOURCE_ID,
            state="active",
        )

        response: dict = await self.gateway.create_campaign(request_data)
        campaign_id = response.get("id")

        if not campaign_id:
            raise HTTPException(status_code=500, detail="Failed to create campaign")
