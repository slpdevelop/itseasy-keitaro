from datetime import datetime
from uuid import UUID

from app.schemas.base import Base
from pydantic import BaseModel, ConfigDict, Field


# Kept for existing campaign-related schemas/API compatibility.
class OfferResponse(Base):
    """Minimal offer response for legacy campaign-offer operations.

    Contains only essential fields (id and name) used in older endpoints
    that reference offers within campaigns or group-level settings.
    Does not include local database tracking fields (synced, deleted).
    """

    id: int
    name: str


class OfferListResponse(Base):
    """Paginated response for offer listing endpoints.

    Contains array of OfferResponse objects and total count for UI pagination.
    Used by GET /api/v1/offers to display catalog of available offers.
    """

    items: list[OfferResponse]
    total: int


class LocalOfferResponse(Base):
    """Detailed local offer record from database with tracking metadata.

    Represents an offer imported and stored locally with sync flags, timestamps,
    and delete status. Used when UI needs full local state beyond simple id/name.
    """

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    keitaro_id: int
    name: str
    synced: bool
    deleted: bool
    created_at: datetime
    updated_at: datetime

    @property
    def attributes(self):
        """Return attribute names for documentation."""
        return ["id", "keitaro_id", "name", "synced", "deleted", "created_at", "updated_at"]


class LocalOfferListResponse(Base):
    """Paginated response listing all local offer records.

    Used by GET /api/v1/offers/local endpoint with optional include_deleted parameter.
    Contains array of LocalOfferResponse and total count for UI pagination.
    """

    items: list[LocalOfferResponse]
    total: int


class RemoteOffer(BaseModel):
    """Offer as returned by Keitaro `/offers/{id}`.

    Attributes:
        id: Keitaro numeric ID of the offer.
        name: Offer display name.
    """

    model_config = ConfigDict(extra="ignore", frozen=True)

    id: int = Field(gt=0)
    name: str
