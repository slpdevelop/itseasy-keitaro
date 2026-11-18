import logging

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
