"""Business logic for offers from Keitaro and the local database."""

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.repositories.offer_repository import OfferRepository


class OfferService:
    """Business logic for managing offer entities and synchronization.

    Handles operations on offers imported from Keitaro into local database:
    - Fetching offer catalog from Keitaro API
    - Importing individual offers for flow binding
    - Soft delete and restore of local offer records
    - Synchronization status tracking

    Does not create or modify offers in Keitaro itself—only manages
    local references and FlowOffer bindings to streams. Uses dependency
    injection with OfferRepository for persistence operations.

    Attributes:
        gateway: HTTP client gateway for Keitaro API requests.
        repository: OfferRepository for CRUD operations on local offers.
    """

    def __init__(
        self,
        gateway: Any,
        db_session: async_sessionmaker[AsyncSession],
    ) -> None:
        self.gateway = gateway
        self.db_session = db_session

    async def get_keitaro_offers(self) -> Any:
        """Fetch complete offer catalog from Keitaro API.

        Retrieves all active offers available in Keitaro system for potential
        import into local database or display in UI offer selection interfaces.

        Returns:
            Raw response from Keitaro /offers endpoint (structure varies by API version).
        """
        return await self.gateway.get("/offers")

    async def get_local_offers(self, *, include_deleted: bool = False):
        """Retrieve all local offer records (optionally including soft-deleted).

        Fetches offers from repository for UI listing or operations that require
        full local state. Filters out deleted records unless explicitly requested.

        Args:
            include_deleted: If True, return offers with deleted=True flag set.

        Returns:
            List of Offer entities ordered by name. Empty if none found.
        """
        async with self.db_session() as session:
            return await OfferRepository(session).get_all(include_deleted=include_deleted)
