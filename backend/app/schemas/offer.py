from datetime import datetime
from uuid import UUID

from app.schemas.base import Base
from pydantic import BaseModel, ConfigDict, Field


class LocalOfferResponse(Base):
    """Detailed local offer record from database with tracking metadata.

    Represents an offer imported and stored locally with sync flags, timestamps,
    and delete status. Used when UI needs full local state beyond simple id/name.
    """

    id: UUID
    keitaro_id: int
    name: str
    synced: bool
    deleted: bool
    created_at: datetime
    updated_at: datetime


class LocalOfferListResponse(Base):
    """Response listing all local offer records with their total count.

    Used by GET /api/v1/offers/local endpoint with optional include_deleted parameter.
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
