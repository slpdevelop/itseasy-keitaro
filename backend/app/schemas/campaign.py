import secrets
import string
from datetime import datetime
from typing import Literal, LiteralString
from uuid import UUID

from app.schemas.base import Base
from pydantic import BaseModel, Field, field_validator


class KTCampaignCreateRequest(BaseModel):
    """Request body for creating a campaign via Keitaro API.

    Contains minimal required fields for campaign creation with offer bindings.
    Used by POST /api/v1/campaigns endpoint to initiate new campaign in Keitaro.
    """

    name: str = Field(min_length=1, max_length=255)
    country_code: str = Field(min_length=2, max_length=2, pattern=r"^[A-Za-z]{2}$")
    offer_id_list: list[int]

    @field_validator("name")
    @classmethod
    def strip_name(cls, value: str) -> str:
        """Remove leading/trailing whitespace and reject blank names."""
        value = value.strip()
        if not value:
            raise ValueError("Campaign name cannot be blank")
        return value


def generate_code(length: int = 10) -> str:
    """Generate random alphanumeric string for campaign alias.

    Uses cryptographically secure random selection from ASCII letters and digits.

    Args:
        length: Number of characters to generate (default: 10).

    Returns:
        Random string suitable for use as campaign or flow identifier.
    """
    alphabet: LiteralString = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


class CampaignCreatePayload(BaseModel):
    """Application input schema for creating a new campaign.

    Used when building campaign objects locally before sending to Keitaro API.
    Contains all required fields including aliases generated automatically and
    configuration defaults from application settings.
    """

    name: str = Field(min_length=1, max_length=255)
    alias: str = Field(default_factory=generate_code)
    domain_id: int = Field(gt=0)
    group_id: int = Field(gt=0)
    traffic_source_id: int = Field(gt=0)
    state: Literal["active", "disabled", "deleted"] = "active"

    @field_validator("name")
    @classmethod
    def strip_name(cls, value: str) -> str:
        """Remove leading/trailing whitespace and reject blank names."""
        value = value.strip()
        if not value:
            raise ValueError("Campaign name cannot be blank")
        return value


class KTCampaignCreateResponse(Base):
    """Response from campaign creation endpoint.

    Indicates successful creation with campaign ID, prefixed name, and confirmation message.
    Used as response model for POST /api/v1/campaigns returning 201 Created status.
    """

    success: bool = True
    campaign_id: int
    campaign_name: str
    message: str


class CampaignOfferDetailResponse(Base):
    """Offer details embedded in flow bindings within a campaign.

    Contains minimal offer metadata required for display and binding operations.
    Used when nesting offers inside CampaignFlowDetailResponse or CampaignDetailResponse.
    """

    id: UUID
    keitaro_id: int
    name: str


class CampaignFlowOfferDetailResponse(Base):
    """Detailed flow-offer binding within a campaign flow.

    Represents a single offer attached to a flow with traffic share percentage
    and active/disabled state. Nested inside CampaignFlowDetailResponse offers array.
    """

    offer: CampaignOfferDetailResponse
    share: int
    state: str

    @field_validator("state", mode="before")
    @classmethod
    def serialize_state(cls, value: object) -> str:
        """Convert enum or string to plain string for serialization."""
        return value.value if hasattr(value, "value") else str(value)


class CampaignFlowDetailResponse(Base):
    """Complete flow/stream details within a campaign.

    Includes all flow configuration (type, position, schema/action) and nested
    offer bindings. Used in CampaignDetailResponse to display campaign structure.
    """

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
        """Convert enum or string to plain string for serialization."""
        if value is None:
            return None
        return value.value if hasattr(value, "value") else str(value)


class CampaignDetailResponse(Base):
    """Complete campaign details with flows and nested offer bindings.

    Top-level response for GET /api/v1/campaigns/{campaign_id} including all
    associated streams (GEO and OFFER flows) with their active offer allocations.
    Used for displaying full campaign configuration in UI.
    """

    id: UUID
    keitaro_id: int
    name: str
    domain_keitaro_id: int | None
    group_keitaro_id: int | None
    traffic_source_keitaro_id: int | None
    fetched_at: datetime | None
    flows: list[CampaignFlowDetailResponse]
