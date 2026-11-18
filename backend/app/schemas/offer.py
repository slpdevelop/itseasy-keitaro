from pydantic import BaseModel, Field


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
    added: list[int] = []
    removed: list[int] = []
    total: int
    added: list[int] = Field(default_factory=list)
    removed: list[int] = Field(default_factory=list)
