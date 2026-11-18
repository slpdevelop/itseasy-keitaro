from pydantic import BaseModel, Field, ConfigDict, field_validator


class CampaignCreate(BaseModel):
    """Application input for creating a campaign."""

    name: str = Field(min_length=1, max_length=255)
    country_code: str = Field(min_length=2, max_length=2, pattern=r"^[A-Za-z]{2}$")
    offer_id: int = Field(gt=0)
    domain_id: int = Field(gt=0)
    group_id: int = Field(gt=0)
    traffic_source_id: int = Field(gt=0)

    @field_validator("name")
    @classmethod
    def strip_name(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Campaign name cannot be blank")
        return value

    @field_validator("country_code")
    @classmethod
    def normalize_country_code(cls, value: str) -> str:
        return value.upper()


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


class KeitaroCampaignRequest(BaseModel):
    """Fields documented for Keitaro CampaignRequest."""
    alias: str | None = None
    type: str | None = None
    name: str | None = None
    cookies_ttl: int | None = None
    state: str | None = None
    cost_type: str | None = None
    cost_value: float | None = None
    cost_currency: str | None = None
    cost_auto: bool | None = None
    group_id: str | None = None
    bind_visitors: str | None = None
    traffic_source_id: int | None = None
    parameters: dict | None = None
    token: str | None = None
    domain_id: int | None = None
    postbacks: list[dict] | None = None
    notes: str | None = None
