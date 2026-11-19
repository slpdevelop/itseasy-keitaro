from typing import Any, Protocol

from app.schemas.flow import FlowCreate


class FlowGateway(Protocol):
    async def create_flow(self, data: FlowCreate) -> dict: ...

    async def get_campaign_flows(self, campaign_id: int) -> Any: ...

    async def update_flow_offers(self, flow_id: int, offers: list[dict[str, Any]]) -> Any: ...
