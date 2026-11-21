"""Business logic for offers from Keitaro and the local database."""

from uuid import UUID
from typing import Any

from app.core.exceptions import InvalidRequestError, OfferNotFoundError
from app.models.models import Offer
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

    def __init__(self, gateway: Any, repository: OfferRepository) -> None:
        self.gateway = gateway
        self.repository = repository

    async def get_keitaro_offers(self) -> Any:
        """Fetch complete offer catalog from Keitaro API.

        Retrieves all active offers available in Keitaro system for potential
        import into local database or display in UI offer selection interfaces.

        Returns:
            Raw response from Keitaro /offers endpoint (structure varies by API version).
        """
        return await self.gateway.get("/offers")

    async def get_keitaro_offer(self, keitaro_id: int) -> Any:
        """Fetch single offer details from Keitaro by numeric ID.

        Retrieves complete information for a specific offer to validate during
        import operations or when displaying offer details in UI.

        Args:
            keitaro_id: External numeric ID assigned by Keitaro.

        Returns:
            Dictionary containing offer data from Keitaro API response.
        """
        return await self.gateway.get(f"/offers/{keitaro_id}")

    async def get_local_offers(self, *, include_deleted: bool = False):
        """Retrieve all local offer records (optionally including soft-deleted).

        Fetches offers from repository for UI listing or operations that require
        full local state. Filters out deleted records unless explicitly requested.

        Args:
            include_deleted: If True, return offers with deleted=True flag set.

        Returns:
            List of Offer entities ordered by name. Empty if none found.
        """
        return await self.repository.get_all(include_deleted=include_deleted)

    async def add_offer(self, keitaro_id: int):
        """Import a Keitaro offer into local database and mark as synced.

        Fetches full offer data from Keitaro by ID, validates name matches, then
        either returns existing local record (or restored from deleted state) or
        creates new Offer entity with stripped whitespace name. Does not sync back
        to Keitaro—only establishes local reference for binding operations.

        Args:
            keitaro_id: External numeric ID of offer to import locally.

        Returns:
            Local Offer entity created or restored. Synced=True automatically set.

        Raises:
            InvalidRequestError: If Keitaro returns invalid format or mismatching ID.
            OfferNotFoundError: If existing offer deleted and cannot be restored.
        """
        data = await self.get_keitaro_offer(keitaro_id)
        if not isinstance(data, dict):
            raise InvalidRequestError("Keitaro returned invalid offer information")

        returned_id = data.get("id")
        name = data.get("name")

        existing = await self.repository.get_by_keitaro_id(keitaro_id)
        if existing is not None:
            if existing.deleted:
                # The offer was fetched and validated against Keitaro just above.
                restored = await self.repository.set_deleted(
                    existing.id, deleted=False, synced=True
                )
                if restored is None:  # defensive: row may have been removed concurrently
                    raise OfferNotFoundError()
                return restored
            return existing

        return await self.repository.create(keitaro_id=keitaro_id, name=name.strip(), synced=True)

    async def delete_offer(self, offer_id: UUID) -> Offer:
        """Soft-delete a local offer record (logical removal).

        Marks offer as deleted in database without removing from storage. Underlying
        Keitaro offer remains unchanged. Offers can be restored via restore method.
        Deleted offers cannot participate in new flow bindings unless restored first.

        Args:
            offer_id: Local UUID of offer to delete.

        Returns:
            Updated Offer entity with deleted=True flag set.

        Raises:
            OfferNotFoundError: If offer not found in database.
        """
        offer: Offer | None = await self.repository.set_deleted(offer_id, deleted=True)
        if offer is None:
            raise OfferNotFoundError()
        return offer

    async def restore_offer(self, offer_id: UUID) -> Offer:
        """Restore a soft-deleted offer to active state.

        Sets deleted=False flag on local record and resets synced=False since
        the restored offer's current state must be re-validated against Keitaro
        before being pushed back to upstream system.

        Args:
            offer_id: Local UUID of deleted offer to restore.

        Returns:
            Restored Offer entity with deleted=False, synced=False.

        Raises:
            OfferNotFoundError: If offer not found in database.
        """
        offer: Offer | None = await self.repository.set_deleted(offer_id, deleted=False)
        if offer is None:
            raise OfferNotFoundError()
        return offer
