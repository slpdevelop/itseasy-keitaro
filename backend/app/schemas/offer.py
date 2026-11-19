from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


# Kept for existing campaign-related schemas/API compatibility.
class OfferResponse(BaseModel):
    id: int
    name: str


class OfferListResponse(BaseModel):
    items: list[OfferResponse]
    total: int


class CampaignOffersResponse(BaseModel):
    campaign_id: int
    items: list[OfferResponse]
    total: int


class CampaignOffersUpdate(BaseModel):
    offer_ids: list[int] = Field(min_length=1)


class CampaignOffersUpdateResponse(BaseModel):
    campaign_id: int
    added: list[int] = Field(default_factory=list)
    removed: list[int] = Field(default_factory=list)
    total: int


class OfferCreateRequest(BaseModel):
    keitaro_id: int = Field(gt=0)


class LocalOfferResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    keitaro_id: int
    name: str
    synced: bool
    deleted: bool
    created_at: datetime
    updated_at: datetime


class LocalOfferListResponse(BaseModel):
    items: list[LocalOfferResponse]
    total: int


class OfferDeleteResponse(BaseModel):
    id: UUID
    deleted: bool


class OfferRestoreResponse(BaseModel):
    id: UUID
    deleted: bool
    synced: bool
