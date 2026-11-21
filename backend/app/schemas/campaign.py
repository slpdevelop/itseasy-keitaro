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


# keitaro_id: поправьте тип, если у вас str
KeitaroFlowId = int


class SyncErrorStage(StrEnum):
    VALIDATION = "validation"  # не прошла проверка payload до отправки
    PUSH = "push"  # упал вызов Keitaro, ничего не отправлено
    MARK_SYNCED = "mark_synced"  # в Keitaro ушло, но отметка в БД не сохранилась


class SyncError(BaseModel):
    model_config = ConfigDict(frozen=True)

    flow_id: KeitaroFlowId
    stage: SyncErrorStage
    error: str = Field(description="Имя класса исключения")
    message: Annotated[str, StringConstraints(max_length=500)] | None = Field(
        default=None,
        description="Обрезанное сообщение, без секретов и токенов",
    )


class SyncResult(BaseModel):
    campaign_id: KeitaroFlowId = Field(description="Keitaro ID кампании, чьи флоу синхронизировались")
    flows_checked: Annotated[int, Field(ge=0, description="Сколько флоу было в выборке")] = 0
    flows_synced: Annotated[int, Field(ge=0, description="Полностью подтверждены")] = 0
    flows_still_pending: Annotated[
        list[KeitaroFlowId],
        Field(default_factory=list, description="Уйдут на следующем проходе"),
    ]
    flows_not_found: Annotated[
        list[KeitaroFlowId],
        Field(default_factory=list, description="Флоу удалён между выборкой и подтверждением"),
    ]
    errors: Annotated[list[SyncError], Field(default_factory=list)]

    @computed_field  # type: ignore[prop-decorator]
    @property
    def success(self) -> bool:
        """Нет ошибок. Pending не считается ошибкой."""
        return not self.errors

    @computed_field  # type: ignore[prop-decorator]
    @property
    def fully_synced(self) -> bool:
        """Нет ни ошибок, ни хвостов: всё, что было, подтверждено."""
        return not self.errors and not self.flows_still_pending and not self.flows_not_found

    # --- хелперы, чтобы не раскидывать логику по sync_campaign ---

    def add_error(
        self,
        flow_id: KeitaroFlowId,
        stage: SyncErrorStage,
        exc: BaseException,
    ) -> None:
        self.errors.append(
            SyncError(
                flow_id=flow_id,
                stage=stage,
                error=type(exc).__name__,
                message=str(exc)[:500] or None,
            )
        )


class OfferPayload(BaseModel):
    """Один оффер в теле PUT-запроса в Keitaro."""

    model_config = ConfigDict(frozen=True)

    offer_id: int
    share: int = Field(ge=0)
    state: str


class PushedLink(BaseModel):
    """Значения binding на момент отправки. Подтверждаются только при точном совпадении."""

    model_config = ConfigDict(frozen=True)

    share: int
    state: str
    deleted: bool

    @property
    def fingerprint(self) -> tuple[int, str, bool]:
        return (self.share, self.state, self.deleted)


class FlowPush(BaseModel):
    model_config = ConfigDict(frozen=True)

    flow_id: UUID
    keitaro_id: int
    offers: Annotated[
        list[OfferPayload],
        Field(default_factory=list, description="Тело PUT: только не удалённые bindings"),
    ]
    pushed: Annotated[
        dict[UUID, PushedLink],
        Field(
            default_factory=dict,
            description="Все загруженные bindings, включая tombstones: link.id -> значения",
        ),
    ]

    @model_validator(mode="after")
    def check_shares_total(self) -> Self:
        """Keitaro принимает только распределение ровно в 100%; пустой список допустим."""
        if self.offers and sum(offer.share for offer in self.offers) != 100:
            raise ValueError("Offer shares of a flow must total exactly 100")
        return self

    @classmethod
    def from_flow(cls, flow: Any) -> "FlowPush":
        """Строить только внутри открытой сессии: читает flow.offers и link.offer."""
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
        """Формат, который ждёт CampaignRepository.mark_flow_synced."""
        return {link_id: link.fingerprint for link_id, link in self.pushed.items()}
