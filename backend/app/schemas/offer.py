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


class CampaignOffersResponse(Base):
    """Offers response scoped to a specific campaign.

    Returns list of offers configured within a campaign's flow bindings.
    Includes campaign_id reference for context and pagination metadata.
    """

    campaign_id: int
    items: list[OfferResponse]
    total: int


class CampaignOffersUpdate(BaseModel):
    """Request payload to update offer bindings on a campaign.

    Used when modifying which offers should receive traffic from a campaign.
    Contains only the list of Keitaro offer IDs to activate or include.

    Attributes:
        offer_ids: List of offer numeric IDs to add to the campaign flow.
    """

    offer_ids: list[int] = Field(min_length=1)


class CampaignOffersUpdateResponse(Base):
    """Response after updating campaign offer bindings.

    Reports added and removed offer IDs along with total count for confirmation.
    Used by POST /api/v1/campaigns/{id}/offers update endpoint.
    """

    campaign_id: int
    added: list[int] = Field(default_factory=list)
    removed: list[int] = Field(default_factory=list)
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
