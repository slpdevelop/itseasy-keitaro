import secrets
import string
from datetime import datetime
from typing import Literal, LiteralString
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class KTCampaignCreateRequest(BaseModel):
    """Fields documented for Keitaro CampaignRequest."""

    name: str = Field(min_length=1, max_length=255)
    country_code: str = Field(min_length=2, max_length=2, pattern=r"^[A-Za-z]{2}$")
    offer_id_list: list[int]

    @field_validator("name")
    @classmethod
    def strip_name(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Campaign name cannot be blank")
        return value


def generate_code(length: int = 10) -> str:
    alphabet: LiteralString = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


class CampaignCreatePayload(BaseModel):
    """Application input for creating a campaign."""

    name: str = Field(min_length=1, max_length=255)
    alias: str = Field(default_factory=generate_code)
    domain_id: int = Field(gt=0)
    group_id: int = Field(gt=0)
    traffic_source_id: int = Field(gt=0)
    state: Literal["active", "disabled", "deleted"] = "active"

    @field_validator("name")
    @classmethod
    def strip_name(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Campaign name cannot be blank")
        return value


class KTCampaignCreateResponse(BaseModel):
    success: bool = True
    campaign_id: int
    campaign_name: str
    message: str


class CampaignOfferDetailResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    keitaro_id: int
    name: str


class CampaignFlowOfferDetailResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    offer: CampaignOfferDetailResponse
    share: int
    state: str

    @field_validator("state", mode="before")
    @classmethod
    def serialize_state(cls, value: object) -> str:
        return value.value if hasattr(value, "value") else str(value)


class CampaignFlowDetailResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: UUID
    keitaro_id: int
    name: str
    type: str | None
    position: int
    schema_: str | None = Field(alias="schema")
    action_type: str | None
    action_payload: str | None
    country: str | None
    offers: list[CampaignFlowOfferDetailResponse]

    @field_validator("type", mode="before")
    @classmethod
    def serialize_type(cls, value: object) -> str | None:
        if value is None:
            return None
        return value.value if hasattr(value, "value") else str(value)


class CampaignDetailResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    keitaro_id: int
    name: str
    domain_keitaro_id: int | None
    group_keitaro_id: int | None
    traffic_source_keitaro_id: int | None
    fetched_at: datetime | None
    flows: list[CampaignFlowDetailResponse]
