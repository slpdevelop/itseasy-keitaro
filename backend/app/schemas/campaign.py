import secrets
import string
from datetime import datetime
from enum import StrEnum
from typing import Annotated, Any, Literal, LiteralString, Self
from uuid import UUID

from app.schemas.base import Base
from pydantic import (
    AliasPath,
    BaseModel,
    ConfigDict,
    Field,
    StringConstraints,
    computed_field,
    field_validator,
    model_validator,
)


class KTCampaignCreateRequest(BaseModel):
    """Request body for creating a campaign via Keitaro API.

    Args:
        name: Campaign name (1-255 characters).
        country_code: Two-letter country code.
        offer_id_list: 1-100 unique Keitaro offer IDs to bind (traffic is split
            equally; 100 is the limit because shares are whole percents).

    Used by POST /api/v1/campaigns to initiate a new campaign in Keitaro.
    """

    name: str = Field(min_length=1, max_length=255)
    country_code: str = Field(min_length=2, max_length=2, pattern=r"^[A-Za-z]{2}$")
    offer_id_list: list[Annotated[int, Field(gt=0)]] = Field(min_length=1, max_length=100)

    @field_validator("offer_id_list")
    @classmethod
    def offer_ids_unique(cls, value: list[int]) -> list[int]:
        """Reject duplicate offer IDs."""
        if len(set(value)) != len(value):
            raise ValueError("Offer IDs must be unique")
        return value

    @field_validator("name")
    @classmethod
    def strip_name(cls, value: str) -> str:
        """Strip whitespace and reject blank names.

        Args:
            value: Raw campaign name.

        Returns:
            Stripped campaign name.

        Raises:
            ValueError: If the name is blank after stripping.
        """
        value = value.strip()
        if not value:
            raise ValueError("Campaign name cannot be blank")
        return value


def generate_code(length: int = 10) -> str:
    """Generate a random alphanumeric campaign alias.

    Args:
        length: Number of characters in the generated string (default: 10).

    Returns:
        Random string suitable for use as a campaign or flow identifier.
    """
    alphabet: LiteralString = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


class CampaignCreatePayload(BaseModel):
    """Application input schema for building a campaign before sending to Keitaro.

    Contains all required fields including an auto-generated alias and
    configuration defaults taken from application settings.

    Args:
        name: Campaign name (1-255 characters).
        alias: Auto-generated campaign alias.
        domain_id: Keitaro domain ID.
        group_id: Keitaro group ID.
        traffic_source_id: Keitaro traffic source ID.
        state: Campaign state, one of active/disabled/deleted (default: active).
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
        """Strip whitespace and reject blank names.

        Args:
            value: Raw campaign name.

        Returns:
            Stripped campaign name.

        Raises:
            ValueError: If the name is blank after stripping.
        """
        value = value.strip()
        if not value:
            raise ValueError("Campaign name cannot be blank")
        return value


class KTCampaignCreateResponse(Base):
    """Response from the campaign creation endpoint.

    Attributes:
        success: Whether creation succeeded (default: True).
        campaign_id: Numeric Keitaro campaign ID.
        campaign_name: Campaign name with prefix applied.
        message: Human-readable confirmation message.

    Used as the response model for POST /api/v1/campaigns (201 Created).
    """

    success: bool = True
    campaign_id: int
    campaign_name: str
    message: str


class CampaignOfferDetailResponse(Base):
    """Offer details embedded in flow bindings within a campaign.

    Contains minimal offer metadata needed for display and binding operations.

    Attributes:
        id: Local database UUID of the offer.
        keitaro_id: Keitaro numeric offer ID.
        name: Offer display name.
    """

    id: UUID
    keitaro_id: int
    name: str


class CampaignFlowOfferDetailResponse(Base):
    """Detailed flow-offer binding within a campaign flow.

    Represents a single offer attached to a flow with traffic share percentage
    and active/disabled state. Nested inside CampaignFlowDetailResponse.offers.
    """

    offer: CampaignOfferDetailResponse
    offer_id: int = Field(validation_alias=AliasPath("offer", "keitaro_id"))
    keitaro_id: int = Field(validation_alias=AliasPath("offer", "keitaro_id"))
    name: str = Field(validation_alias=AliasPath("offer", "name"))
    share: int
    pinned: bool = False
    state: str
    deleted: bool = False
    synced: bool = False

    @field_validator("state", mode="before")
    @classmethod
    def serialize_state(cls, value: object) -> str:
        """Convert an enum or string value to a plain string for serialization.

        Args:
            value: Raw state value (enum member or string).

        Returns:
            String representation of the state.
        """
        return value.value if hasattr(value, "value") else str(value)


class CampaignFlowDetailResponse(Base):
    """Complete flow/stream details within a campaign.

    Includes flow configuration (type, position, schema/action) and nested
    offer bindings. Used in CampaignFlowDetailResponse to display campaign structure.

    Attributes:
        id: Local database UUID of the flow.
        keitaro_id: Keitaro numeric flow ID.
        name: Flow display name.
        type: Flow type (e.g., "geo", "offer").
        position: Flow position index.
        schema_: Flow schema alias (e.g., "redirect", "landings").
        action_type: Keitaro action type.
        action_payload: Flow action payload as text.
        country: Two-letter country code for GEO flows, if any.
        offers: List of offer bindings attached to this flow.
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
        """Convert an enum or string value to a plain string for serialization.

        Args:
            value: Raw type value (enum member, string, or None).

        Returns:
            String representation of the type, or None if the value is None.
        """
        if value is None:
            return None
        return value.value if hasattr(value, "value") else str(value)


class CampaignDetailResponse(Base):
    """Complete campaign details with flows and nested offer bindings.

    Top-level response for GET /api/v1/campaigns/{campaign_id}, including all
    associated streams (GEO and OFFER flows) with their offer allocations.
    Used for displaying full campaign configuration in the UI.

    Attributes:
        id: Local database UUID of the campaign.
        keitaro_id: Keitaro numeric campaign ID.
        name: Campaign name.
        domain_keitaro_id: Keitaro domain ID, if assigned.
        group_keitaro_id: Keitaro group ID, if assigned.
        traffic_source_keitaro_id: Keitaro traffic source ID, if assigned.
        fetched_at: Timestamp when the campaign was last fetched from Keitaro.
        flows: List of flows belonging to this campaign.
    """

    id: UUID
    keitaro_id: int
    name: str
    domain_keitaro_id: int | None
    group_keitaro_id: int | None
    traffic_source_keitaro_id: int | None
    fetched_at: datetime | None
    flows: list[CampaignFlowDetailResponse]


class RemoteCampaign(BaseModel):
    """Campaign as returned by Keitaro `/campaigns/{id}`.

    Attributes:
        id: Keitaro numeric ID of the campaign.
        name: Campaign name (with prefix).
        domain_id: Keitaro domain ID, if assigned.
        group_id: Keitaro group ID, if assigned.
        traffic_source_id: Keitaro traffic source ID, if assigned.
    """

    model_config = ConfigDict(extra="ignore", frozen=True)

    id: int = Field(gt=0)
    name: str
    domain_id: int | None = None
    group_id: int | None = None
    traffic_source_id: int | None = None


KeitaroId = int


class SyncErrorStage(StrEnum):
    """Stages at which a sync error can occur."""

    VALIDATION = "validation"  # payload validation failed before sending
    PUSH = "push"  # Keitaro call failed, nothing sent
    MARK_SYNCED = "mark_synced"  # sent to Keitaro but DB mark not saved


class SyncError(BaseModel):
    """Error record for a single flow during sync.

    Attributes:
        flow_id: Keitaro numeric ID of the flow where the error occurred.
        stage: Sync stage where the error happened.
        error: Exception class name.
        message: Trimmed error message, without secrets or tokens (max 500 chars).
    """

    model_config = ConfigDict(frozen=True)

    flow_id: KeitaroId
    stage: SyncErrorStage
    error: str = Field(description="Exception class name")
    message: Annotated[str, StringConstraints(max_length=500)] | None = Field(
        default=None,
        description="Trimmed message, without secrets and tokens",
    )


class SyncResult(BaseModel):
    """Result of a per-campaign flow sync operation.

    Attributes:
        campaign_id: Keitaro ID of the campaign whose flows were synced.
        flows_checked: Number of flows examined during sync.
        flows_synced: Number of flows fully confirmed as synced.
        flows_still_pending: Flow IDs that still need another sync pass.
        flows_not_found: Flow IDs deleted between selection and confirmation.
        errors: Per-flow error records.
    """

    campaign_id: KeitaroId = Field(
        description="Keitaro ID of the campaign whose flows were synced"
    )
    flows_checked: Annotated[int, Field(ge=0, description="Number of flows in the sample")] = 0
    flows_synced: Annotated[int, Field(ge=0, description="Fully confirmed")] = 0
    flows_still_pending: Annotated[
        list[KeitaroId],
        Field(default_factory=list, description="Will go on the next pass"),
    ]
    flows_not_found: Annotated[
        list[KeitaroId],
        Field(default_factory=list, description="Flow deleted between selection and confirmation"),
    ]
    errors: Annotated[list[SyncError], Field(default_factory=list)]

    @computed_field  # type: ignore[prop-decorator]
    @property
    def success(self) -> bool:
        """True if no errors occurred (pending flows are not counted as errors)."""
        return not self.errors

    @computed_field  # type: ignore[prop-decorator]
    @property
    def fully_synced(self) -> bool:
        """True if no errors and no pending or not-found flows remain."""
        return not self.errors and not self.flows_still_pending and not self.flows_not_found

    def add_error(
        self,
        flow_id: KeitaroId,
        stage: SyncErrorStage,
        exc: BaseException,
    ) -> None:
        """Record an error for a flow at a given sync stage.

        Args:
            flow_id: Keitaro numeric ID of the flow.
            stage: Sync stage where the error occurred.
            exc: Exception that was raised.
        """
        self.errors.append(
            SyncError(
                flow_id=flow_id,
                stage=stage,
                error=type(exc).__name__,
                message=str(exc)[:500] or None,
            )
        )


class OfferPayload(BaseModel):
    """One offer in the PUT request body to Keitaro.

    Attributes:
        offer_id: Keitaro numeric offer ID.
        share: Traffic share percentage (must be >= 0).
        state: Offer state string (e.g., "active", "disabled").
    """

    model_config = ConfigDict(frozen=True)

    offer_id: int
    share: int = Field(ge=0)
    state: str


class PushedLink(BaseModel):
    """Binding values captured at the time of sending to Keitaro.

    Confirmed only on exact match during mark_flow_synced.

    Attributes:
        share: Traffic share percentage.
        state: Offer state string.
        deleted: Whether the binding was marked as deleted.
    """

    model_config = ConfigDict(frozen=True)

    share: int
    state: str
    deleted: bool

    @property
    def fingerprint(self) -> tuple[int, str, bool]:
        """Return the (share, state, deleted) tuple used for comparison."""
        return (self.share, self.state, self.deleted)


class FlowPush(BaseModel):
    """Snapshot of a flow's offer bindings prepared for pushing to Keitaro.

    Attributes:
        flow_id: Local database UUID of the flow.
        keitaro_id: Keitaro numeric flow ID.
        offers: Offer payloads for the PUT body (non-deleted bindings only).
        pushed: All loaded bindings including tombstones, keyed by link UUID.
    """

    model_config = ConfigDict(frozen=True)

    flow_id: UUID
    keitaro_id: int
    offers: Annotated[
        list[OfferPayload],
        Field(default_factory=list, description="PUT body: only non-deleted bindings"),
    ]
    pushed: Annotated[
        dict[UUID, PushedLink],
        Field(
            default_factory=dict,
            description="All loaded bindings, including tombstones: link.id -> values",
        ),
    ]

    @model_validator(mode="after")
    def check_shares_total(self) -> Self:
        """Validate that offer shares total exactly 100%.

        Keitaro accepts only exactly 100% distribution; an empty offer list is allowed.

        Returns:
            The validated FlowPush instance.

        Raises:
            ValueError: If offers are non-empty and shares do not total 100.
        """
        if self.offers and sum(offer.share for offer in self.offers) != 100:
            raise ValueError("Offer shares of a flow must total exactly 100")
        return self

    @classmethod
    def from_flow(cls, flow: Any) -> "FlowPush":
        """Build a FlowPush from an ORM flow instance.

        Must be called within an open session so flow.offers and link.offer
        are accessible.

        Args:
            flow: ORM Flow instance with loaded offers relationship.

        Returns:
            FlowPush populated from the flow's bindings.
        """
        return cls(
            flow_id=flow.id,
            keitaro_id=flow.keitaro_id,
            offers=[
                OfferPayload(
                    offer_id=link.offer.keitaro_id,
                    share=link.share,
                    state=link.state.value,
                )
                for link in flow.offers
                if not link.deleted
            ],
            pushed={
                link.id: PushedLink(
                    share=link.share,
                    state=link.state.value,
                    deleted=link.deleted,
                )
                for link in flow.offers
            },
        )

    @property
    def pushed_fingerprints(self) -> dict[UUID, tuple[int, str, bool]]:
        """Return link fingerprints in the format expected by
        CampaignRepository.mark_flow_synced."""
        return {link_id: link.fingerprint for link_id, link in self.pushed.items()}
