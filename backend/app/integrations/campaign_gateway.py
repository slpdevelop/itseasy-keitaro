from app.integrations.keitaro import KeitaroGateway
from app.schemas.campaign import CampaignCreatePayload


class KeitaroCampaignGateway:
    def __init__(self, gateway: KeitaroGateway) -> None:
        self.gateway = gateway

    async def get_campaigns(self) -> list[dict]:
        return await self.gateway.get("/campaigns")

    async def create_campaign(self, data: CampaignCreatePayload) -> dict:
        return await self.gateway.post("/campaigns", data.model_dump(exclude_none=True))

    async def delete_campaign(self, campaign_id: int) -> None:
        await self.gateway.delete(f"/campaigns/{campaign_id}")

    async def get_by_id(self, campaign_id: int) -> None:
        return await self.gateway.get(f"/campaigns/{campaign_id}")
