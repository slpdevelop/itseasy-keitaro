from datetime import datetime
import enum
import uuid

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


def _enum_values(enum_cls: type[enum.Enum]) -> list[str]:
    """Convert enum class to list of value strings for SQLAlchemy Enum.

    Maps enum members (e.g., FlowType.GEO) to their raw string values
    ("geo", "offer") for database storage compatibility.

    Args:
        enum_cls: Enum class to convert.

    Returns:
        List of enum member values as strings.
    """
    return [member.value for member in enum_cls]


class Base(DeclarativeBase):
    """SQLAlchemy declarative base for all model classes.

    Provides common column configuration, naming conventions, and relationship
    setup. All database models inherit from this base to enable unified metadata
    management via Alembic migrations.

    Attributes:
        __table__: Automatically generated table metadata for each subclass.
        __bind__: Database engine connection (set in application config).
    """


class BaseModel(Base):
    """Base mixin with common database columns and sync tracking.

    All local entities inherit these fields: unique UUID primary key,
    timestamps for creation/update, and flags for synchronization status.
    Used as abstract base for all table models.

    Attributes:
        id: Unique locally-generated UUID identifier.
        created_at: Timestamp when record was first created.
        updated_at: Timestamp of last modification (auto-updated).
        synced: Whether this entity has been synchronized with Keitaro.
        deleted: Soft-delete flag; True means logically removed but stored.
    """

    __abstract__ = True

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()  # pylint: disable=not-callable
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),  # pylint: disable=not-callable
        onupdate=func.now(),  # pylint: disable=not-callable
    )
    synced: Mapped[bool] = mapped_column(default=False)
    deleted: Mapped[bool] = mapped_column(default=False)


class KeitaroEntityMixin:
    """Mixin for entities that exist in Keitaro and have numeric IDs.

    Provides shared fields linking to Keitaro's global identifier system.
    Used by Campaign, Flow, and Offer models to reference external systems.

    Attributes:
        keitaro_id: Numeric ID assigned by Keitaro (external reference).
        fetched_at: Timestamp when this entity was last retrieved from Keitaro.
    """

    keitaro_id: Mapped[int] = mapped_column(Integer, unique=True, index=True)
    fetched_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Campaign(KeitaroEntityMixin, BaseModel):
    """Local representation of a Keitaro campaign entity.

    Stores campaign metadata including name, associated group/domain/traffic source,
    and relationships to flows. Each campaign has exactly one GEO flow (for country
    targeting) and optionally multiple OFFER flows with binding configurations.

    Relationships:
        flows: One-to-many relation; a campaign contains multiple streams.
    """

    __tablename__ = "campaigns"

    name: Mapped[str] = mapped_column(String(255))

    domain_keitaro_id: Mapped[int | None] = mapped_column(Integer)
    group_keitaro_id: Mapped[int | None] = mapped_column(Integer)
    traffic_source_keitaro_id: Mapped[int | None] = mapped_column(Integer)

    flows: Mapped[list["Flow"]] = relationship(
        back_populates="campaign",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="Flow.position",
    )
    """List of flows belonging to this campaign (GEO and OFFER)."""


class FlowType(enum.Enum):
    """Enum for flow/stream types in Keitaro."""

    GEO = "geo"
    OFFER = "offer"


# pylint: disable=unsubscriptable-object


class Flow(KeitaroEntityMixin, BaseModel):
    """Represents a campaign stream/flow in Keitaro.

    Each campaign has multiple flows: one GEO flow for country targeting and
    one or more OFFER flows containing offer bindings. Flows define how traffic
    is routed to specific configurations based on location or offers.

    Constraints:
        - Country field limited to 2 characters (ISO code) when set.
        - Cascade delete from parent campaign removes all flows.

    Relationships:
        campaign: Belongs to exactly one Campaign.
        offers: One-to-many relation; a flow can have multiple offer bindings.
    """

    __tablename__ = "flows"
    __table_args__ = (
        CheckConstraint("country IS NULL OR length(country) = 2", name="ck_flows_country_len"),
    )

    campaign_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("campaigns.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(255))
    type: Mapped[FlowType | None] = mapped_column(
        Enum(FlowType, name="flow_type", values_callable=_enum_values)
    )
    position: Mapped[int] = mapped_column(Integer, default=0)

    schema: Mapped[str | None] = mapped_column(String(64))
    action_type: Mapped[str | None] = mapped_column(String(64))
    action_payload: Mapped[str | None] = mapped_column(Text)
    country: Mapped[str | None] = mapped_column(String(2))

    campaign: Mapped["Campaign"] = relationship(back_populates="flows")
    offers: Mapped[list["FlowOffer"]] = relationship(
        back_populates="flow",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class Offer(KeitaroEntityMixin, BaseModel):
    """Local representation of a Keitaro offer entity.

    Stores metadata for offers available in the Keitaro system. These are not
    created or modified by this application—only imported for tracking and
    binding them to flows via FlowOffer relationships. Offers remain unchanged
    in Keitaro; only their flow associations are synchronized.

    Attributes:
        name: Display name of the offer in Keitaro.
    """

    __tablename__ = "offers"

    name: Mapped[str] = mapped_column(String(255))
    """Offer display name from Keitaro (max 255 characters)."""


class FlowOfferState(enum.Enum):
    """Enum for offer binding states in Keitaro."""

    ACTIVE = "active"
    DISABLED = "disabled"


class FlowOffer(BaseModel):
    """Represents an offer binding to a specific flow.

    This is the central entity for traffic distribution: it links a Flow
    to an Offer with a traffic share percentage (0-100) and state. Each flow
    can have multiple bindings, but only ACTIVE ones receive traffic.

    Constraints:
        - Unique pair of (flow_id, offer_id); prevents duplicate bindings.
        - Share must be between 0 and 100 inclusive.
        - Cascade delete from Flow removes binding; Offer deletion is restricted.

    Relationships:
        flow: Belongs to exactly one Flow.
        offer: References a single Offer entity.
    """

    __tablename__ = "flow_offers"
    __table_args__ = (
        UniqueConstraint("flow_id", "offer_id", name="uq_flow_offers_flow_offer"),
        CheckConstraint("share BETWEEN 0 AND 100", name="ck_flow_offers_share_range"),
    )

    flow_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("flows.id", ondelete="CASCADE"))
    offer_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("offers.id", ondelete="RESTRICT"), index=True
    )
    share: Mapped[int] = mapped_column(Integer)
    pinned: Mapped[bool] = mapped_column(default=False, server_default="false")
    state: Mapped[FlowOfferState] = mapped_column(
        Enum(FlowOfferState, name="flow_offer_state", values_callable=_enum_values),
        default=FlowOfferState.ACTIVE,
    )

    flow: Mapped["Flow"] = relationship(back_populates="offers")
    offer: Mapped["Offer"] = relationship()
