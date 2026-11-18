from app.interfaces.campaign_gateway import CampaignGateway
from app.schemas.campaign import CampaignCreate
from app.schemas.offer import OfferResponse


class CampaignService:

    def __init__(self, gateway: CampaignGateway):
        self.gateway = gateway

    async def create_campaign(
        self,
        data: CampaignCreate,
    ) -> dict:
        return await self.gateway.create_campaign(data)

    async def delete_campaign(
        self,
        campaign_id: int,
    ) -> None:
        await self.gateway.delete_campaign(campaign_id)

    async def get_offers(self) -> list[OfferResponse]:
        return await self.gateway.get_offers()

    async def get_campaign_offers(
        self,
        campaign_id: int,
    ) -> list[OfferResponse]:
        return await self.gateway.get_campaign_offers(campaign_id)

    async def add_offers(
        self,
        campaign_id: int,
        offer_ids: list[int],
    ) -> list[int]:
        return await self.gateway.add_offers(
            campaign_id,
            offer_ids,
        )

    async def remove_offers(
        self,
        campaign_id: int,
        offer_ids: list[int],
    ) -> list[int]:
        return await self.gateway.remove_offers(
            campaign_id,
            offer_ids,
        )
