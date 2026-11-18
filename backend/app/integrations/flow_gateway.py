import logging

from app.integrations.keitaro import KeitaroGateway
from app.interfaces.flow_gateway import FlowGateway
from app.schemas.flow import FlowCreate

logger: logging.Logger = logging.getLogger(__name__)


class KeitaroFlowGateway(FlowGateway):

    def __init__(self, gateway: KeitaroGateway):
        self.gateway: KeitaroGateway = gateway


async def create_flow(self, data: FlowCreate) -> dict:
    logger.info(f"ZAZAZAZAZA {data.model_dump(exclude_none=True)}")
    return await self.gateway.post(
        "/streams",
        data.model_dump(exclude_none=True),
    )
