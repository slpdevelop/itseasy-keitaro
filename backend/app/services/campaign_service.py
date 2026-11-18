import logging
from typing import TYPE_CHECKING

from app.core.config import Settings
from app.core.exceptions import CampaignCreationError, InvalidRequestError
from app.schemas.campaign import (
    CampaignCreate,
    CampaignCreateResponse,
    KeitaroCampaignCreateRequest,
)

if TYPE_CHECKING:
    from app.services.flow_service import FlowService
    from app.interfaces.campaign_gateway import CampaignGateway

logger = logging.getLogger(__name__)


class CampaignService:
    def __init__(
        self, gateway: "CampaignGateway", flow_service: "FlowService", settings: Settings
    ) -> None:
        self.gateway = gateway
        self.flow_service = flow_service
        self.settings = settings

    async def get_campaigns(self) -> list[dict]:
        campaigns = await self.gateway.get_campaigns()
        return [
            campaign
            for campaign in campaigns
            if (campaign.get("name") or "").startswith(self.settings.campaign_name_prefix)
        ]

    async def create_campaign(self, data: KeitaroCampaignCreateRequest) -> CampaignCreateResponse:
        campaign_name: str = data.name
        if not campaign_name.startswith(self.settings.campaign_name_prefix):
            campaign_name = f"{self.settings.campaign_name_prefix}{campaign_name}"
        if len(campaign_name) > 255:
            raise InvalidRequestError("Campaign name exceeds the 255-character Keitaro limit")

        request_data = CampaignCreate(
            name=campaign_name,
            domain_id=self.settings.campaign_domain_id,
            group_id=self.settings.campaign_group_id,
            traffic_source_id=self.settings.campaign_traffic_source_id,
            state="active",
        )

        response = await self.gateway.create_campaign(request_data)
        campaign_id = response.get("id") if isinstance(response, dict) else None
        if not isinstance(campaign_id, int) or campaign_id <= 0:
            raise CampaignCreationError("Keitaro did not return a valid campaign id")

        try:
            await self.flow_service.create_geo_flow(campaign_id, data.country_code)
            await self.flow_service.create_offer_flow(campaign_id, data.offer_id_list)
        except Exception as exc:
            try:
                await self.gateway.delete_campaign(campaign_id)
                logger.warning("Rolled back campaign %s after flow creation failure", campaign_id)
            except Exception:
                logger.exception(
                    "Failed to roll back campaign %s after flow creation failure", campaign_id
                )
                raise CampaignCreationError(
                    "Flow creation failed and campaign cleanup also failed; manual cleanup is required"
                ) from exc
            raise

        return CampaignCreateResponse(
            campaign_id=campaign_id,
            campaign_name=campaign_name,
            message="Campaign and flows successfully created",
        )
