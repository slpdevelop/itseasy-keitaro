"""Persistence operations for locally managed Keitaro offers."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.models.models import Offer


class OfferRepository:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def get_all(self, *, include_deleted: bool = False) -> list[Offer]:
        async with self._session_factory() as session:
            statement = select(Offer).order_by(Offer.name)
            if not include_deleted:
                statement = statement.where(Offer.deleted.is_(False))
            result = await session.execute(statement)
            return list(result.scalars().all())

    async def get_by_id(self, offer_id: UUID) -> Offer | None:
        async with self._session_factory() as session:
            result = await session.execute(select(Offer).where(Offer.id == offer_id))
            return result.scalar_one_or_none()

    async def get_by_keitaro_id(self, keitaro_id: int) -> Offer | None:
        async with self._session_factory() as session:
            result = await session.execute(
                select(Offer).where(Offer.keitaro_id == keitaro_id)
            )
            return result.scalar_one_or_none()

    async def create(self, *, keitaro_id: int, name: str) -> Offer:
        async with self._session_factory() as session, session.begin():
            offer = Offer(
                keitaro_id=keitaro_id,
                name=name,
                synced=False,
                deleted=False,
            )
            session.add(offer)
            await session.flush()
            await session.refresh(offer)
            return offer

    async def set_deleted(self, offer_id: UUID, *, deleted: bool) -> Offer | None:
        async with self._session_factory() as session, session.begin():
            result = await session.execute(
                select(Offer).where(Offer.id == offer_id).with_for_update()
            )
            offer = result.scalar_one_or_none()
            if offer is None:
                return None

            offer.deleted = deleted
            if not deleted:
                # Restored offers must be synchronized with Keitaro again.
                offer.synced = False

            await session.flush()
            await session.refresh(offer)
            return offer
