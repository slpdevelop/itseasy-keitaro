import json
from typing import Any, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


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
    Used by Service when initiating multi-step campaign creation.
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
    share: int = Field(default=0, ge=0, le=100)
    pinned: bool = False
    # "deleted" is a legacy way to say deleted=true; the binding keeps its real state.
    state: Literal["active", "disabled", "deleted"] = "active"
    deleted: bool = False

    model_config = ConfigDict(extra="ignore")

    @model_validator(mode="after")
    def deleted_state_requires_flag(self) -> Self:
        """The legacy state "deleted" must come together with deleted=true."""
        if self.state == "deleted" and not self.deleted:
            raise ValueError("Deleted state requires deleted=true")
        return self


class FlowOffersUpdateRequest(BaseModel):
    """Payload for replacing the local offer bindings of a flow."""

    offers: list[FlowOfferUpdate]

    model_config = ConfigDict(extra="ignore")

    @field_validator("offers")
    @classmethod
    def offer_ids_unique(cls, value: list[FlowOfferUpdate]) -> list[FlowOfferUpdate]:
        """An offer can be bound to a flow only once."""
        ids = [item.offer_id for item in value]
        if len(set(ids)) != len(ids):
            raise ValueError("An offer cannot be added to the same flow more than once")
        return value


RemoteOfferState = Literal["active", "disabled"]


class RemoteFlowOffer(BaseModel):
    """Offer binding as returned by Keitaro inside a stream.

    Attributes:
        offer_id: Keitaro ID of the offer itself (not the ID of the binding).
        share: Traffic share percentage (0-100).
        state: "active" or "disabled"; Keitaro may send null, which means active.
    """

    model_config = ConfigDict(extra="ignore", frozen=True)

    offer_id: int = Field(gt=0)
    share: int = Field(ge=0, le=100)
    state: RemoteOfferState = "active"

    @field_validator("state", mode="before")
    @classmethod
    def default_state(cls, value: object) -> object:
        """Treat a missing/null state as active."""
        return value or "active"


class RemoteFlow(BaseModel):
    """Flow/stream as returned by Keitaro `/campaigns/{id}/streams`.

    Validates the upstream response once, so the service layer works with typed
    attributes instead of raw dict keys.

    Attributes:
        id: Keitaro numeric ID of the flow.
        name: Flow name; may be empty in Keitaro.
        schema_: Flow schema (e.g. "redirect", "landings").
        action_type: Keitaro action type.
        action_payload: Action payload as text; non-string values are JSON-encoded.
        country: Country code parsed from an accepting "country" filter, if any.
        offers: Offer bindings; empty for GEO flows.
    """

    model_config = ConfigDict(extra="ignore", frozen=True)

    id: int = Field(gt=0)
    name: str = ""
    schema_: str | None = Field(default=None, alias="schema")
    action_type: str | None = None
    action_payload: str | None = None
    country: str | None = None
    offers: list[RemoteFlowOffer] = Field(default_factory=list)

    @model_validator(mode="before")
    @classmethod
    def extract_country(cls, data: Any) -> Any:
        """Derive `country` from the flow filters without failing on unknown filters."""
        if not isinstance(data, dict):
            return data
        country: str | None = None
        for item in data.get("filters") or []:
            if not isinstance(item, dict):
                continue
            payload = item.get("payload")
            if (
                item.get("name") == "country"
                and item.get("mode") == "accept"
                and isinstance(payload, list)
                and len(payload) == 1
                and isinstance(payload[0], str)
                and len(payload[0].strip()) == 2
            ):
                country = payload[0].strip().upper()
                break
        return {**data, "country": country}

    @field_validator("name", mode="before")
    @classmethod
    def default_name(cls, value: object) -> object:
        """Treat a null name as empty."""
        return value or ""

    @field_validator("action_payload", mode="before")
    @classmethod
    def payload_to_text(cls, value: object) -> object:
        """Keep strings as-is and JSON-encode anything else for the TEXT column."""
        if value is None or isinstance(value, str):
            return value
        return json.dumps(value, ensure_ascii=False)

    @field_validator("offers", mode="before")
    @classmethod
    def default_offers(cls, value: object) -> object:
        """Treat null offers as an empty list."""
        return value or []
