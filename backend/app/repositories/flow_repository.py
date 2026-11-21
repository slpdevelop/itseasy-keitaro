"""Persistence operations for locally managed Keitaro offers."""

from app.models.models import Flow
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload


class FlowRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_by_campaign(self, campaign_id: int) -> list[Flow]:
        stmt = (
            select(Flow).where(Flow.campaign_id == campaign_id).options(selectinload(Flow.offers))
        )
        return list((await self._session.scalars(stmt)).all())

    def add(self, flow: Flow) -> None:
        self._session.add(flow)

    async def delete(self, flow: Flow) -> None:
        await self._session.delete(flow)  # FlowOffer удалятся через delete-orphan

    async def flush(self) -> None:
        await self._session.flush()
