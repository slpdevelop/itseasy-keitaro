"""Business logic for offers from Keitaro and the local database."""

from uuid import UUID
from typing import Any

from app.core.exceptions import InvalidRequestError, OfferNotFoundError
from app.repositories.offer_repository import OfferRepository


class OfferService:
    def __init__(self, gateway: Any, repository: OfferRepository) -> None:
        self.gateway = gateway
        self.repository = repository

    async def get_keitaro_offers(self) -> Any:
        """Return the current offer catalogue from Keitaro."""
        return await self.gateway.get("/offers")

    async def get_keitaro_offer(self, keitaro_id: int) -> Any:
        return await self.gateway.get(f"/offers/{keitaro_id}")

    async def get_local_offers(self, *, include_deleted: bool = False):
        return await self.repository.get_all(include_deleted=include_deleted)

    async def add_offer(self, keitaro_id: int):
        """Import one Keitaro offer locally; this does not sync it back to Keitaro."""
        data = await self.get_keitaro_offer(keitaro_id)
        if not isinstance(data, dict):
            raise InvalidRequestError("Keitaro returned invalid offer information")

        returned_id = data.get("id")
        name = data.get("name")
        if returned_id != keitaro_id or not isinstance(name, str) or not name.strip():
            raise InvalidRequestError("Keitaro returned invalid offer information")

        existing = await self.repository.get_by_keitaro_id(keitaro_id)
        if existing is not None:
            if existing.deleted:
                restored = await self.repository.set_deleted(existing.id, deleted=False)
                if restored is None:  # defensive: row may have been removed concurrently
                    raise OfferNotFoundError()
                return restored
            return existing

        return await self.repository.create(keitaro_id=keitaro_id, name=name.strip())

    async def delete_offer(self, offer_id: UUID):
        offer = await self.repository.set_deleted(offer_id, deleted=True)
        if offer is None:
            raise OfferNotFoundError()
        return offer

    async def restore_offer(self, offer_id: UUID):
        offer = await self.repository.set_deleted(offer_id, deleted=False)
        if offer is None:
            raise OfferNotFoundError()
        return offer
