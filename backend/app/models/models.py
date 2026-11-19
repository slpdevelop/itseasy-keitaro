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
    return [member.value for member in enum_cls]


class Base(DeclarativeBase):
    pass


class BaseModel(Base):
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
    keitaro_id: Mapped[int] = mapped_column(Integer, unique=True, index=True)
    fetched_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Campaign(KeitaroEntityMixin, BaseModel):
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


class FlowType(enum.Enum):
    GEO = "geo"
    OFFER = "offer"


class Flow(KeitaroEntityMixin, BaseModel):
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
    __tablename__ = "offers"

    name: Mapped[str] = mapped_column(String(255))


class FlowOfferState(enum.Enum):
    ACTIVE = "active"
    DISABLED = "disabled"


class FlowOffer(BaseModel):
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
    state: Mapped[FlowOfferState] = mapped_column(
        Enum(FlowOfferState, name="flow_offer_state", values_callable=_enum_values),
        default=FlowOfferState.ACTIVE,
    )

    flow: Mapped["Flow"] = relationship(back_populates="offers")
    offer: Mapped["Offer"] = relationship()
