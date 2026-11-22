from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Mapping
from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from sqlalchemy.sql.selectable import Select

from app.core.exceptions import CampaignCreationError, FlowNotFoundError
from app.models.models import Campaign, Flow, FlowOffer, FlowOfferState, FlowType, Offer
from app.schemas.campaign import RemoteCampaign
from app.schemas.flow import FlowOfferUpdate
from app.domain.flow_offers import apply_offer_updates


class CampaignRepository:
    """Repository for campaign CRUD operations and local synchronization.

    Handles all SQLAlchemy queries and transactions related to Campaign entities,
    including flows and flow offer bindings. Uses async sessions with context
    managers for automatic transaction handling via `session.begin()`.

    All methods are async to support non-blocking I/O during database operations.
    Session factory is injected at construction for reusing connection pooling.

    Attributes:
        _session: AsyncSession scoped to the caller's transaction.
    """

    def __init__(self, session: AsyncSession):
        """Initialize repository with the request/operation-scoped session.

        Args:
            session: Active SQLAlchemy async session owned by the service layer.
        """
        self._session: AsyncSession = session

    async def create_or_update_campaign(
        self, remote: RemoteCampaign, *, fetched_at: datetime
    ) -> Campaign:
        """Upsert a local campaign projection from the Keitaro response.

        Overwrites all Keitaro-owned fields, marks the campaign as synced and
        restores it if it was soft-deleted locally. Flushes so the returned entity
        has its local UUID assigned.

        Args:
            remote: Validated campaign data from Keitaro.
            fetched_at: Timestamp of the fetch, shared with flows and offers of the
                same operation.

        Returns:
            Created or updated Campaign entity.
        """
        campaign = await self._get_by_keitaro_id(self._session, Campaign, remote.id)
        if campaign is None:
            campaign = Campaign(keitaro_id=remote.id)
            self._session.add(campaign)

        campaign.name = remote.name
        campaign.domain_keitaro_id = remote.domain_id
        campaign.group_keitaro_id = remote.group_id
        campaign.traffic_source_keitaro_id = remote.traffic_source_id
        campaign.fetched_at = fetched_at
        campaign.synced = True
        campaign.deleted = False
        await self._session.flush()
        return campaign

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
        """Persist a newly created campaign with its flows and offer bindings.

        Atomically saves campaign entity, creates upserts for GEO and OFFER flows,
        then attaches all offer bindings to the OFFER flow. Creates Offer stubs
        if referenced offers don't exist locally yet. Marks flows as synced after save.

        Uses transaction block with `session.begin()` for atomicity; rollback on error.

        Args:
            keitaro_id: Numeric ID of campaign from Keitaro response.
            name: Display name for the campaign.
            domain/group/traffic_source_keitaro_ids: Reference IDs for campaign metadata.
            country_code: ISO 2-letter code for GEO flow targeting.
            geo_flow: Dictionary containing GEO flow data (id, name, position).
            offer_flow: Dictionary with OFFER flow data and list of offer bindings.

        Raises:
            CampaignCreationError: If Keitaro returns invalid flow IDs during save.
        """
        now: datetime = datetime.now(timezone.utc)
        campaign = await self._get_by_keitaro_id(self._session, Campaign, keitaro_id)
        if campaign is None:
            campaign = Campaign(keitaro_id=keitaro_id)
            self._session.add(campaign)
        campaign.name = name
        campaign.domain_keitaro_id = domain_keitaro_id
        campaign.group_keitaro_id = group_keitaro_id
        campaign.traffic_source_keitaro_id = traffic_source_keitaro_id
        campaign.fetched_at = now
        await self._session.flush()
        await self._upsert_flow(
            self._session, campaign, geo_flow, FlowType.GEO, country_code.upper(), now
        )
        flow = await self._upsert_flow(
            self._session, campaign, offer_flow, FlowType.OFFER, None, now
        )
        await self._upsert_flow_offers(self._session, flow, offer_flow.get("offers") or [])
        flow.synced = True

    async def get_campaign_detail(self, keitaro_id: int) -> Campaign | None:
        """Retrieve a campaign with all nested flows and offer bindings.

        Executes a single SELECT with JOINs to load the complete campaign tree:
        Campaign → Flows (GEO/OFFER) → FlowOffer bindings → Offer entities.
        Uses selectinload for efficient eager loading of related data.

        Args:
            keitaro_id: Numeric ID of campaign to fetch.

        Returns:
            Full Campaign entity with flows and offers loaded, or None if not found.
        """
        query: Select[tuple[Campaign]] = (
            select(Campaign)
            .where(Campaign.keitaro_id == keitaro_id)
            .options(
                selectinload(Campaign.flows).selectinload(Flow.offers).selectinload(FlowOffer.offer)
            )
        )
        result = await self._session.execute(query)
        return result.scalar_one_or_none()


    async def update_flow_offers(
        self, flow_id: UUID, items: list[FlowOfferUpdate]
    ) -> Flow | None:
        """Load and lock a flow, then persist domain-normalized offer bindings."""
        session = self._session
        flow = await session.scalar(
            select(Flow)
            .where(Flow.id == flow_id, Flow.deleted.is_(False))
            .options(
                selectinload(Flow.offers).selectinload(FlowOffer.offer),
                selectinload(Flow.campaign),
            )
            .with_for_update(of=Flow)
        )
        if flow is None:
            return None
        offer_ids = [item.offer_id for item in items]
        offers = []
        if offer_ids:
            offers = list(
                (await session.execute(select(Offer).where(Offer.keitaro_id.in_(offer_ids))))
                .scalars().all()
            )
        by_keitaro_id = {offer.keitaro_id: offer for offer in offers}
        missing = set(offer_ids) - by_keitaro_id.keys()
        for missing_id in sorted(missing):
            offer = Offer(keitaro_id=missing_id, name=f"Offer {missing_id}", synced=True)
            session.add(offer)
            by_keitaro_id[missing_id] = offer
        if missing:
            await session.flush()

        apply_offer_updates(flow, items, by_keitaro_id)
        await session.flush()
        return flow

    async def get_by_keitaro_id(self, keitaro_id: int) -> Campaign | None:
        """Fetch a local campaign by its Keitaro numeric ID (without nested data).

        Args:
            keitaro_id: Numeric ID of the campaign in Keitaro.

        Returns:
            Campaign entity if stored locally, None otherwise.
        """
        return await self._get_by_keitaro_id(self._session, Campaign, keitaro_id)

    async def get_flows_pending_sync(self, campaign_id: UUID) -> list[Flow]:
        """Fetch OFFER flows of one campaign needing push sync to Keitaro.

        Returns flows of the campaign where either Flow.synced=False or any
        FlowOffer binding has synced=False. Excludes GEO flows and soft-deleted
        flows. Uses EXISTS subquery to find flows with dirty bindings without
        full JOINs.

        Args:
            campaign_id: Local UUID of the campaign (Campaign.id, not keitaro_id).

        Returns:
            List of Flow entities with nested offers loaded for payload building.
        """
        dirty_link = (
            select(FlowOffer.id)
            .where(
                FlowOffer.flow_id == Flow.id,
                FlowOffer.synced.is_(False),
            )
            .exists()
        )
        query = (
            select(Flow)
            .where(
                Flow.campaign_id == campaign_id,
                Flow.deleted.is_(False),
                Flow.type == FlowType.OFFER,
            )
            .where(or_(Flow.synced.is_(False), dirty_link))
            .options(
                selectinload(Flow.offers).selectinload(FlowOffer.offer),
                selectinload(Flow.campaign),
            )
            .order_by(Flow.keitaro_id)
        )
        return list((await self._session.execute(query)).scalars().unique().all())

    async def mark_flow_synced(
        self,
        flow_id: UUID,
        pushed: Mapping[UUID, tuple[int, str, bool]],
    ) -> bool:
        """Confirm exactly the bindings that were pushed; True if flow is fully synced.

        Soft-deleted bindings are confirmed like any other (deleted=True, synced=True)
        and are excluded from subsequent loads by the pending filter.
        """
        flow = await self._session.scalar(
            select(Flow)
            .where(Flow.id == flow_id)
            .with_for_update()
            .execution_options(populate_existing=True)
        )
        if flow is None:
            raise FlowNotFoundError("Flow not found")

        links = (
            await self._session.scalars(
                select(FlowOffer)
                .where(
                    FlowOffer.flow_id == flow_id,
                    or_(FlowOffer.deleted.is_(False), FlowOffer.synced.is_(False)),
                )
                .with_for_update()
                .execution_options(populate_existing=True)
            )
        ).all()

        fully_synced = True
        for link in links:
            if pushed.get(link.id) == (link.share, link.state.value, link.deleted):
                link.synced = True
            else:
                link.synced = False
                fully_synced = False

        flow.synced = fully_synced
        await self._session.flush()
        return fully_synced

    @staticmethod
    async def _get_by_keitaro_id(session: AsyncSession, model, keitaro_id: int):
        """Fetch single entity by Keitaro numeric ID.

        Generic helper used throughout repository to look up Campaign, Flow, or Offer
        by their external identifier. Avoids repeating select() + where() patterns.

        Args:
            session: Active SQLAlchemy async session.
            model: SQLAlchemy ORM class (Campaign, Flow, or Offer).
            keitaro_id: External numeric ID from Keitaro.

        Returns:
            Entity instance if found, None otherwise.
        """
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
        """Create or update a flow entity from Keitaro response data.

        Implements upsert pattern: checks if flow exists by keitaro_id, creates if not,
        then overwrites all fields except id (UUID). Validates that returned ID is valid
        integer > 0; raises CampaignCreationError otherwise.

        Args:
            session: Active SQLAlchemy async session.
            campaign: Parent Campaign entity for relationship assignment.
            data: Dictionary of flow attributes from Keitaro API response.
            flow_type: Enum classification (GEO or OFFER).
            country: Country code for GEO flows, None for OFFER flows.
            now: Timestamp to set on fetched_at field.

        Returns:
            Flow entity created or updated.

        Raises:
            CampaignCreationError: If Keitaro returns invalid flow ID.
        """
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
        """Attach or update offer bindings for a flow.

        Upserts FlowOffer entities linking the flow to offers referenced in Keitaro response.
        Creates Offer stubs if references don't exist locally yet (full data loaded later).
        Marks all new/updated bindings as synced and non-deleted. Ignores empty items list.

        Args:
            session: Active SQLAlchemy async session.
            flow: Parent Flow entity to attach bindings to.
            items: List of dicts with offer_id, share, state from Keitaro response.
        """
        if not items:
            return

        keitaro_ids = [int(item["offer_id"]) for item in items]
        offers = (
            (await session.execute(select(Offer).where(Offer.keitaro_id.in_(keitaro_ids))))
            .scalars()
            .all()
        )
        offers_by_keitaro_id = {offer.keitaro_id: offer for offer in offers}

        # Create stubs for offers not yet locally synced (name will be populated later)
        missing = sorted(set(keitaro_ids) - offers_by_keitaro_id.keys())
        for keitaro_id in missing:
            offer = Offer(keitaro_id=keitaro_id, name=f"Offer {keitaro_id}", synced=True)
            session.add(offer)
            offers_by_keitaro_id[keitaro_id] = offer
        if missing:
            await session.flush()  # Need offer.id for foreign keys

        existing_result = await session.execute(
            select(FlowOffer)
            .options(selectinload(FlowOffer.offer))
            .where(FlowOffer.flow_id == flow.id)
        )
        existing_links = existing_result.scalars().all()
        by_offer_id = {link.offer_id: link for link in existing_links}

        for item in items:
            offer = offers_by_keitaro_id[int(item["offer_id"])]
            link = by_offer_id.get(offer.id)
            if link is None:
                link = FlowOffer(flow_id=flow.id, offer_id=offer.id)
                session.add(link)
                by_offer_id[offer.id] = link
            link.share = int(item["share"])
            link.state = FlowOfferState(item.get("state") or FlowOfferState.ACTIVE.value)
            link.synced = True
            link.deleted = False
        await session.flush()

    @staticmethod
    def _to_text(value: Any) -> str | None:
        """Convert JSON-serializable value to string for Text column.

        Used for flow.action_payload which is TEXT type. Returns as-is if string or None,
        otherwise JSON-encodes the object with ASCII=False for UTF-8 safety.

        Args:
            value: Any value (dict, list, str, or None).

        Returns:
            String representation or original string/None unchanged.
        """
        if value is None or isinstance(value, str):
            return value
        return json.dumps(value, ensure_ascii=False)
