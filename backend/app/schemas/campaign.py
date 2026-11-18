import secrets
import string
from typing import Literal, LiteralString

from app.constants import CAMPAIGN_NAME_PREFIX
from pydantic import BaseModel, Field, ConfigDict, field_validator


class KeitaroCampaignCreateRequest(BaseModel):
    """Fields documented for Keitaro CampaignRequest."""

    name: str = Field(min_length=1, max_length=255)
    country_code: str = Field(min_length=2, max_length=2, pattern=r"^[A-Za-z]{2}$")
    offer_id_list: list[int]

    @field_validator("name")
    @classmethod
    def strip_name(cls, value: str) -> str:
        if not value.startswith(CAMPAIGN_NAME_PREFIX):
            value = f"{CAMPAIGN_NAME_PREFIX}{value}"
        return value


def generate_code(length: int = 10) -> str:
    alphabet: LiteralString = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


class CampaignCreate(BaseModel):
    """Application input for creating a campaign."""

    name: str = Field(min_length=1, max_length=255)
    alias: str = Field(default_factory=generate_code)
    # country_code: str = Field(min_length=2, max_length=2, pattern=r"^[A-Za-z]{2}$")
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


class CampaignResponse(BaseModel):
    model_config = ConfigDict(extra="allow")
    id: int | None = None
    name: str | None = None


class CampaignDeleteResponse(BaseModel):
    id: int
    deleted: bool


class KeitaroResourceListResponse(BaseModel):
    """Pass-through wrapper for Keitaro list responses."""

    items: list[dict]
    total: int
