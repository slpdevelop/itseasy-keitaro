"""Persistence operations for locally stored Keitaro flows."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.models import Flow


class FlowRepository:
    """Repository for local flow entities (streams of a campaign)."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_by_campaign(self, campaign_id: UUID) -> list[Flow]:
        """Load all flows of a campaign (including soft-deleted) with their bindings.

        Args:
            campaign_id: Local UUID of the campaign (Campaign.id, not keitaro_id).

        Returns:
            Flows with ``offers`` eagerly loaded.
        """
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
