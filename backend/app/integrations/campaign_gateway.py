from app.interfaces.campaign_gateway import CampaignGateway
from app.integrations.keitaro import KeitaroGateway
from app.schemas.campaign import CampaignCreate


class KeitaroCampaignGateway(CampaignGateway):

    def __init__(self, gateway: KeitaroGateway):
        self.gateway: KeitaroGateway = gateway

    async def get_campaigns(self) -> list[dict]:
        return await self.gateway.get("/campaigns")

    async def create_campaign(self, data: CampaignCreate) -> list[dict]:
        return await self.gateway.post("/campaigns", data.model_dump(exclude_none=True))
