from asyncio import Protocol

from app.schemas.flow import FlowCreate


class FlowGateway(Protocol):

    async def create_flow(
        self,
        data: FlowCreate,
    ) -> dict: ...
