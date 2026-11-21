"""Persistence operations for locally managed Keitaro offers."""

from collections.abc import Collection
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import Offer
from app.schemas.offer import RemoteOffer


class OfferRepository:
    """Repository for CRUD operations on local offer entities.

    Handles all database queries and transactions related to Offer models.
    Offers are not created or modified in Keitaro by this application—they
    represent existing offers imported into the local system for tracking
    and binding them to flows via FlowOffer entities.

    All methods use async sessions with context managers for atomic operations.
    Soft-delete (deleted=True) is tracked but does not affect Keitaro data.

    Attributes:
        _session: AsyncSession scoped to the caller's transaction.
    """

    def __init__(self, session: AsyncSession) -> None:
        """Initialize repository with the request/operation-scoped session.

        Args:
            session: Active SQLAlchemy async session owned by the service layer.
        """
        self._session = session

    async def get_map_by_keitaro_ids(self, keitaro_ids: Collection[int]) -> dict[int, Offer]:
        ids = set(keitaro_ids)
        if not ids:
            return {}
        stmt = select(Offer).where(Offer.keitaro_id.in_(ids))
        offers = (await self._session.scalars(stmt)).all()
        return {o.keitaro_id: o for o in offers}

    async def get_all(self, *, include_deleted: bool = False) -> list[Offer]:
        """Retrieve all offers from local database (optionally including deleted).

        Loads offer entities ordered by name. Filters out soft-deleted records
        unless explicitly requested via `include_deleted=true`. Used for listing
        available offers in UI and importing into flows.

        Args:
            include_deleted: If True, return offers with deleted=True flag set.

        Returns:
            List of Offer entities sorted by name ascending. Empty if none found.
        """
        statement = select(Offer).order_by(Offer.name)
        if not include_deleted:
            statement = statement.where(Offer.deleted.is_(False))
        result = await self._session.execute(statement)
        return list(result.scalars().all())

    async def get_missing_keitaro_ids(self, keitaro_ids: set[int]) -> set[int]:
        if not keitaro_ids:
            return set()
        query = select(Offer.keitaro_id).where(Offer.keitaro_id.in_(keitaro_ids))
        existing = set(await self._session.scalars(query))
        return keitaro_ids - existing

    async def bulk_create(
        self,
        offers: list[RemoteOffer],
        *,
        synced: bool = True,
        fetched_at: datetime | None = None,
    ) -> list[Offer]:
        """Create local offer records from Keitaro offers in a single flush.

        Callers must pass only offers that do not exist locally yet
        (see ``get_missing_keitaro_ids``); keitaro_id is unique.

        Args:
            offers: Validated offers from Keitaro.
            synced: Whether the records are known to match Keitaro. Default True.
            fetched_at: Timestamp of the fetch to store on every record.

        Returns:
            Created Offer entities with database-assigned UUIDs.
        """
        new_offers: list[Offer] = [
            Offer(
                keitaro_id=offer.id,
                name=offer.name,
                synced=synced,
                deleted=False,
                fetched_at=fetched_at,
            )
            for offer in offers
        ]

        self._session.add_all(new_offers)
        await self._session.flush()
        return new_offers
