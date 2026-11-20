from pydantic import BaseModel, ConfigDict, Field


class FlowFilter(BaseModel):
    """Flow filter configuration used in campaign stream rules.

    Defines filtering criteria that determine whether traffic matches
    a specific flow condition (e.g., geographic location). Used when
    creating flows with targeted audience rules.

    Attributes:
        name: Display name for the filter rule.
        mode: Filtering mode (AND/OR logic between multiple filters).
        payload: Array of filter conditions in Keitaro format.
    """

    name: str
    mode: str
    payload: list[str]


class FlowOffer(BaseModel):
    """Offer binding within a flow's traffic distribution.

    Represents how much traffic share (percentage) an offer receives
    and whether it is currently active or disabled. Used when creating
    OFFER-type flows with multiple offer allocations.

    Attributes:
        offer_id: Keitaro numeric ID of the associated offer.
        share: Traffic share percentage (0-100).
        state: "active" to receive traffic, "disabled" to exclude.
    """

    offer_id: int
    share: int
    state: str = "active"


class FlowCreate(BaseModel):
    """Request payload for creating a new flow/stream in Keitaro.

    Contains complete configuration for stream including type (GEO/OFFER),
    positioning, filtering schema, action rules, and optional offer bindings.
    Used by CampaignService when initiating multi-step campaign creation.
    """

    model_config = ConfigDict(extra="forbid")

    campaign_id: int
    name: str
    type: str = "regular"
    schema_: str = Field(alias="schema")
    action_type: str = "http"
    action_payload: str = ""
    collect_clicks: bool = True

    filters: list[FlowFilter] | None = None
    offers: list[FlowOffer] | None = None


class FlowOfferUpdate(BaseModel):
    """Offer binding sent by the UI when editing an OFFER flow."""

    offer_id: int = Field(gt=0)
    share: float = Field(default=0, ge=0, le=100)
    state: str = "active"
    deleted: bool = False

    model_config = ConfigDict(extra="ignore")


class FlowOffersUpdateRequest(BaseModel):
    """Payload for replacing the local offer bindings of a flow."""

    offers: list[FlowOfferUpdate]

    model_config = ConfigDict(extra="ignore")
