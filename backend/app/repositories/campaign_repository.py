from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.models.models import Campaign, Flow, FlowOffer, FlowOfferState, FlowType, Offer


class CampaignCreationError(Exception):
    pass


class CampaignRepository:

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]):
        self._session_factory = session_factory

    async def save_created_campaign(
        self,
        *,
        keitaro_id: int,
        name: str,
        domain_keitaro_id: int | None,
        group_keitaro_id: int | None,
        traffic_source_keitaro_id: int | None,
        country_code: str,
        geo_flow: dict[str, Any],
        offer_flow: dict[str, Any],
    ) -> None:
        now = datetime.now(timezone.utc)
        async with self._session_factory() as session, session.begin():
            campaign = await self._get_by_keitaro_id(session, Campaign, keitaro_id)
            if campaign is None:
                campaign = Campaign(keitaro_id=keitaro_id)
                session.add(campaign)
            campaign.name = name
            campaign.domain_keitaro_id = domain_keitaro_id
            campaign.group_keitaro_id = group_keitaro_id
            campaign.traffic_source_keitaro_id = traffic_source_keitaro_id
            campaign.fetched_at = now
            await session.flush()

            await self._upsert_flow(
                session, campaign, geo_flow, FlowType.GEO, country_code.upper(), now
            )
            flow = await self._upsert_flow(session, campaign, offer_flow, FlowType.OFFER, None, now)
            await self._upsert_flow_offers(session, flow, offer_flow.get("offers") or [])

    # ------------------------------------------------------------------ helpers

    @staticmethod
    async def _get_by_keitaro_id(session: AsyncSession, model, keitaro_id: int):
        result = await session.execute(select(model).where(model.keitaro_id == keitaro_id))
        return result.scalar_one_or_none()

    async def _upsert_flow(
        self,
        session: AsyncSession,
        campaign: Campaign,
        data: dict[str, Any],
        flow_type: FlowType,
        country: str | None,
        now: datetime,
    ) -> Flow:
        keitaro_id = data.get("id") if isinstance(data, dict) else None
        if not isinstance(keitaro_id, int) or keitaro_id <= 0:
            raise CampaignCreationError(f"Keitaro did not return a valid {flow_type.value} flow id")

        flow = await self._get_by_keitaro_id(session, Flow, keitaro_id)
        if flow is None:
            flow = Flow(keitaro_id=keitaro_id)
            session.add(flow)
        flow.campaign_id = campaign.id
        flow.name = str(data.get("name") or flow_type.value)
        flow.type = flow_type
        flow.position = int(data.get("position") or 0)
        flow.schema = data.get("schema")
        flow.action_type = data.get("action_type")
        flow.action_payload = self._to_text(data.get("action_payload"))
        flow.country = country
        flow.fetched_at = now
        await session.flush()
        return flow

    async def _upsert_flow_offers(
        self, session: AsyncSession, flow: Flow, items: list[dict[str, Any]]
    ) -> None:
        if not items:
            return

        keitaro_ids = [int(item["offer_id"]) for item in items]
        offers = (
            (await session.execute(select(Offer).where(Offer.keitaro_id.in_(keitaro_ids))))
            .scalars()
            .all()
        )
        offers_by_keitaro_id = {offer.keitaro_id: offer for offer in offers}

        # Offer.name обязателен, а в ответе Keitaro его нет, поэтому офферы должны
        # быть уже синхронизированы в локальную таблицу offers.
        missing = sorted(set(keitaro_ids) - offers_by_keitaro_id.keys())
        if missing:
            raise CampaignCreationError(f"Offers {missing} are not found in the local DB")

        existing = (
            (await session.execute(select(FlowOffer).where(FlowOffer.flow_id == flow.id)))
            .scalars()
            .all()
        )
        by_offer_id = {link.offer_id: link for link in existing}

        for item in items:
            offer = offers_by_keitaro_id[int(item["offer_id"])]
            link = by_offer_id.get(offer.id)
            if link is None:
                link = FlowOffer(flow_id=flow.id, offer_id=offer.id)
                session.add(link)
            link.share = int(item["share"])
            link.state = FlowOfferState(item.get("state") or FlowOfferState.ACTIVE.value)
        await session.flush()

    @staticmethod
    def _to_text(value: Any) -> str | None:
        if value is None or isinstance(value, str):
            return value
        return json.dumps(value, ensure_ascii=False)
