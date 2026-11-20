"""Persistence operations for locally managed Keitaro offers."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.models.models import Offer


class OfferRepository:
    """Repository for CRUD operations on local offer entities.

    Handles all database queries and transactions related to Offer models.
    Offers are not created or modified in Keitaro by this application—they
    represent existing offers imported into the local system for tracking
    and binding them to flows via FlowOffer entities.

    All methods use async sessions with context managers for atomic operations.
    Soft-delete (deleted=True) is tracked but does not affect Keitaro data.

    Attributes:
        _session_factory: Async session maker using shared engine from app state.
    """

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        """Initialize repository with SQLAlchemy session factory.

        Args:
            session_factory: Async session maker configured with engine and settings.
        """
        self._session_factory = session_factory

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
        async with self._session_factory() as session:
            statement = select(Offer).order_by(Offer.name)
            if not include_deleted:
                statement = statement.where(Offer.deleted.is_(False))
            result = await session.execute(statement)
            return list(result.scalars().all())

    async def get_by_id(self, offer_id: UUID) -> Offer | None:
        """Fetch a single offer entity by local UUID.

        Retrieves complete offer record including synced/deleted flags for
        validation or UI restoration operations. Does not include Keitaro API data.

        Args:
            offer_id: Local database UUID of the offer to fetch.

        Returns:
            Offer entity if found, None otherwise.
        """
        async with self._session_factory() as session:
            result = await session.execute(select(Offer).where(Offer.id == offer_id))
            return result.scalar_one_or_none()

    async def get_by_keitaro_id(self, keitaro_id: int) -> Offer | None:
        """Fetch a single offer by its external Keitaro numeric ID.

        Used when importing offers from Keitaro—matches on external identifier
        rather than local UUID for validation or upsert operations.

        Args:
            keitaro_id: External numeric ID assigned by Keitaro.

        Returns:
            Offer entity if found locally, None otherwise (offer may not be imported yet).
        """
        async with self._session_factory() as session:
            result = await session.execute(select(Offer).where(Offer.keitaro_id == keitaro_id))
            return result.scalar_one_or_none()

    async def create(self, *, keitaro_id: int, name: str) -> Offer:
        """Create a new offer record in the local database.

        Used when importing offers from Keitaro that don't exist locally yet.
        Marks the entity as not synced (synced=False) since it needs to fetch
        full details and validate against upstream data later.

        Args:
            keitaro_id: External numeric ID to assign to the new offer.
            name: Display name for the offer.

        Returns:
            Created Offer entity with database-assigned UUID. Synced=False initially.
        """
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
        """Update soft-delete flag for an offer and sync state accordingly.

        When restoring a deleted offer (deleted=False), automatically marks it as
        unsynced since its current state must be re-validated against Keitaro before
        pushing changes back. Deletion does not affect synced flag.

        Args:
            offer_id: Local UUID of the offer to update.
            deleted: True to soft-delete, False to restore the offer.

        Returns:
            Updated Offer entity with new deleted and synced values, or None if not found.
        """
        async with self._session_factory() as session, session.begin():
            result = await session.execute(
                select(Offer).where(Offer.id == offer_id).with_for_update()
            )
            offer = result.scalar_one_or_none()
            if offer is None:
                return None

            offer.deleted = deleted
            if not deleted:
                offer.synced = False

            await session.flush()
            await session.refresh(offer)
            return offer
