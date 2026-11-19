from datetime import datetime
import enum
from typing import Optional
import uuid

from sqlalchemy import UUID, DateTime, Enum, ForeignKey, Integer, func, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class BaseDBModel(DeclarativeBase):
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    fetched_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()  # pylint: disable=not-callable
    )


class Campaign(BaseDBModel):

    __tablename__ = "campaigns"

    keitaro_id: Mapped[int] = mapped_column(Integer, unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255))


class FlowType(enum.Enum):
    GEO = "geo"
    OFFER = "offer"


class Flow(BaseDBModel):
    __tablename__ = "flows"

    campaign_id: Mapped[int] = mapped_column(ForeignKey("campaigns.id", ondelete="CASCADE"))
    keitaro_id: Mapped[int] = mapped_column(Integer, unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255))
    type: Mapped[FlowType] = mapped_column(Enum(FlowType, name="campaign_status"), nullable=True)
    schema: Mapped[str] = mapped_column(String(255))
    action_type: Mapped[str] = mapped_column(String(255))
    action_payload: Mapped[str] = mapped_column(String(255))
    country: Mapped[str] = mapped_column(String(255))


class FlowOffer(BaseDBModel):
    __tablename__ = "stream_offers"

    flow_id: Mapped[int] = mapped_column(ForeignKey("flows.id", ondelete="CASCADE"))
    offer_id: Mapped[int] = mapped_column(ForeignKey("offer.id", ondelete="CASCADE"))
    share: Mapped[str] = mapped_column(String(255))
    state: Mapped[str] = mapped_column(String(255))


class Offer(BaseDBModel):
    __tablename__ = "offer"

    keitaro_id: Mapped[int] = mapped_column(Integer, unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255))
