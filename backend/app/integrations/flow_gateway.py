import logging
from typing import Any

from app.integrations.keitaro import KeitaroGateway
from app.schemas.flow import FlowCreate

logger: logging.Logger = logging.getLogger(__name__)


class KeitaroFlowGateway:
    def __init__(self, gateway: KeitaroGateway) -> None:
        self.gateway: KeitaroGateway = gateway

    async def create_flow(self, data: FlowCreate) -> dict:
        return await self.gateway.post(
            "/streams", data.model_dump(exclude_none=True, by_alias=True)
        )

    async def get_campaign_flows(self, campaign_id: int) -> Any:
        return await self.gateway.get(f"/campaigns/{campaign_id}/streams")

    async def update_flow_offers(self, flow_id: int, offers: list[dict[str, Any]]) -> Any:
        # StreamRequestPut accepts an update payload; only offers are changed so that
        # unrelated stream settings remain untouched.
        return await self.gateway.put(f"/streams/{flow_id}", {"offers": offers})
