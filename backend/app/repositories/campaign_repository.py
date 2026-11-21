from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import or_, select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import Campaign, Flow, FlowOffer, FlowOfferState, FlowType, Offer
from app.core.exceptions import CampaignCreationError
from sqlalchemy.sql.selectable import Select


class CampaignRepository:
    """Repository for campaign CRUD operations and local synchronization.

    Handles all SQLAlchemy queries and transactions related to Campaign entities,
    including flows and flow offer bindings. Uses async sessions with context
    managers for automatic transaction handling via `session.begin()`.

    All methods are async to support non-blocking I/O during database operations.
    Session factory is injected at construction for reusing connection pooling.

    Attributes:
        _session_factory: Async session maker using shared engine from app state.
    """

    def __init__(self, session: AsyncSession):
        """Initialize repository with SQLAlchemy session factory.

        Args:
            session_factory: Async session maker configured with engine and settings.
        """
        self._session: AsyncSession = session

    async def create_or_update_campaign(self, keitaro_campaign: dict) -> Campaign:
        now: datetime = datetime.now(timezone.utc)
        campaign = await self._get_by_keitaro_id(self._session, Campaign, keitaro_campaign["id"])
        if not campaign:
            campaign = Campaign(keitaro_id=keitaro_campaign["id"])
            self._session.add(campaign)

        campaign.name = keitaro_campaign["name"]
        campaign.domain_keitaro_id = keitaro_campaign["domain_id"]
        campaign.group_keitaro_id = keitaro_campaign["group_id"]
        campaign.traffic_source_keitaro_id = keitaro_campaign["traffic_source_id"]
        campaign.fetched_at = now
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
        async with self._session_factory() as session:
            query: Select[tuple[Campaign]] = (
                select(Campaign)
                .where(Campaign.keitaro_id == keitaro_id)
                .options(
                    selectinload(Campaign.flows)
                    .selectinload(Flow.offers)
                    .selectinload(FlowOffer.offer)
                )
            )
            result = await session.execute(query)
            return result.scalar_one_or_none()

    async def get_local_campaign_streams(self) -> list[dict[str, Any]]:
        """Get tracked campaigns with their active flow IDs for sync operations.

        Returns a filtered list of non-deleted campaigns and their non-deleted flows.
        Used by FlowService to identify which campaign streams need synchronization.
        Does not include offer bindings—only top-level flow references.

        Args:
            None

        Returns:
            List of dicts with keitaro_id and array of active flow objects (id, keitaro_id).
        """
        async with self._session_factory() as session:
            query = (
                select(Campaign)
                .where(Campaign.deleted.is_(False))
                .options(selectinload(Campaign.flows))
            )
            campaigns = (await session.execute(query)).scalars().unique().all()
            return [
                {
                    "keitaro_id": campaign.keitaro_id,
                    "flows": [
                        {"id": flow.id, "keitaro_id": flow.keitaro_id}
                        for flow in campaign.flows
                        if not flow.deleted
                    ],
                }
                for campaign in campaigns
            ]

    async def sync_flow_offers_from_keitaro(
        self,
        flow_keitaro_id: int,
        items: list[dict[str, Any]],
        *,
        offer_names: dict[int, str] | None = None,
        conflicts: list[int] | None = None,
    ) -> bool:
        """Replace local offer bindings with authoritative data from Keitaro.

        Implements pull sync: fetches current offers for a specific flow from Keitaro
        response and updates the local FlowOffer entities accordingly. Creates Offer
        stubs for offers not yet imported locally. Bindings missing from the remote list
        are soft-deleted, matching the UI deletion behavior and preserving their history.

        Local changes that have not been pushed yet (FlowOffer.synced=False) are never
        overwritten: the local version wins until it is pushed with sync-to-keitaro.
        A pending binding that already matches Keitaro is simply marked as synced.
        Pending bindings that differ from Keitaro are reported through ``conflicts``.

        Args:
            flow_keitaro_id: Numeric ID of flow to update bindings for.
            items: List of offer dicts from Keitaro with offer_id, share, and state.
            offer_names: Optional Keitaro offer names used to replace placeholders.
            conflicts: Optional output list; Keitaro IDs of offers whose pending local
                changes were kept instead of being overwritten are appended to it.

        Returns:
            True if flow was found and bindings were updated; False if not found.
        """
        now = datetime.now(timezone.utc)
        async with self._session_factory() as session, session.begin():
            flow = await self._get_by_keitaro_id(session, Flow, flow_keitaro_id)
            if flow is None:
                return False

            offer_ids = [int(item["offer_id"]) for item in items]
            offers = []
            if offer_ids:
                offers = (
                    (await session.execute(select(Offer).where(Offer.keitaro_id.in_(offer_ids))))
                    .scalars()
                    .all()
                )
            offers_by_keitaro_id = {offer.keitaro_id: offer for offer in offers}
            offer_names = offer_names or {}

            # Create records for unknown offers, using the real Keitaro name
            # whenever the service was able to resolve it.
            for missing_id in sorted(set(offer_ids) - offers_by_keitaro_id.keys()):
                name = offer_names.get(missing_id) or f"Offer {missing_id}"
                offer = Offer(keitaro_id=missing_id, name=name, synced=True)
                session.add(offer)
                offers_by_keitaro_id[missing_id] = offer

            # Earlier versions could have stored placeholder names. Replace those
            # with the current name returned by Keitaro.
            for keitaro_id, name in offer_names.items():
                offer = offers_by_keitaro_id.get(keitaro_id)
                if offer is not None and name.strip():
                    offer.name = name.strip()
            if offer_ids:
                await session.flush()

            existing_links = (
                (
                    await session.execute(
                        select(FlowOffer)
                        .options(selectinload(FlowOffer.offer))
                        .where(FlowOffer.flow_id == flow.id)
                    )
                )
                .scalars()
                .all()
            )
            links_by_offer_id = {link.offer_id: link for link in existing_links}
            remote_offer_ids: set[Any] = set()
            conflicts = conflicts if conflicts is not None else []

            for item in items:
                offer = offers_by_keitaro_id[int(item["offer_id"])]
                remote_offer_ids.add(offer.id)
                remote_share = int(item["share"])
                remote_state = FlowOfferState(item.get("state") or FlowOfferState.ACTIVE.value)
                link = links_by_offer_id.get(offer.id)
                if link is None:
                    link = FlowOffer(flow_id=flow.id, offer_id=offer.id)
                    session.add(link)
                    links_by_offer_id[offer.id] = link
                elif link.synced is False:
                    # Unpushed local edit: do not overwrite it with the remote copy.
                    if (link.deleted, link.share, link.state) == (
                        False,
                        remote_share,
                        remote_state,
                    ):
                        link.synced = True  # local edit equals the remote state
                    else:
                        conflicts.append(offer.keitaro_id)
                    continue
                link.share = remote_share
                link.state = remote_state
                link.synced = True
                link.deleted = False

            # Keep bindings that disappeared from Keitaro, but mark them as deleted.
            # This mirrors UI deletion: the relation remains in the database and can
            # still be displayed/restored instead of being physically removed.
            for link in existing_links:
                if link.offer_id in remote_offer_ids:
                    continue
                if link.synced is False:
                    # Pending local change. A binding added locally and not pushed yet
                    # is absent in Keitaro by definition and must not be dropped.
                    if link.deleted:
                        link.synced = True  # local deletion already matches Keitaro
                    else:
                        conflicts.append(link.offer.keitaro_id)
                    continue
                link.deleted = True
                link.share = 0
                link.pinned = False
                link.synced = True

            # The flow stays "pending" while any of its bindings still has local edits.
            flow.synced = not any(link.synced is False for link in links_by_offer_id.values())
            flow.fetched_at = now
            await session.flush()
            return True

    async def update_flow_offers(self, flow_id, items: list[dict[str, Any]]) -> Flow | None:
        """Persist flow offer bindings, including soft-delete and restore state.

        The path identifier is the local Flow UUID. Offer identifiers in the
        payload are numeric Keitaro IDs. Shares are normalized to integer
        percentages that total exactly 100 across non-deleted bindings.

        Sync flags: a binding (and its flow) is marked ``synced=False`` only when
        something Keitaro actually stores has changed: the binding is new, or its
        share, state or deleted flag differs from the value before this call.
        ``pinned`` is local-only metadata (it is not sent to Keitaro), so changing it
        alone does not create a pending sync. A flag is never set back to True here;
        bindings that were already pending stay pending.
        """
        async with self._session_factory() as session, session.begin():
            # Lock the flow row so a concurrent push (mark_flow_synced) cannot
            # interleave with this read-modify-write.
            flow = await session.scalar(
                select(Flow)
                .where(Flow.id == flow_id, Flow.deleted.is_(False))
                .options(selectinload(Flow.offers).selectinload(FlowOffer.offer))
                .with_for_update(of=Flow)
            )
            if flow is None:
                return None
            if flow.type != FlowType.OFFER:
                raise ValueError("Offers can only be changed on OFFER flows")

            offer_ids = [int(item["offer_id"]) for item in items]
            if len(offer_ids) != len(set(offer_ids)):
                raise ValueError("Duplicate offer IDs are not allowed in one flow")

            offers = []
            if offer_ids:
                offers = list(
                    (await session.execute(select(Offer).where(Offer.keitaro_id.in_(offer_ids))))
                    .scalars()
                    .all()
                )
            by_keitaro_id = {offer.keitaro_id: offer for offer in offers}
            for missing_id in sorted(set(offer_ids) - by_keitaro_id.keys()):
                offer = Offer(keitaro_id=missing_id, name=f"Offer {missing_id}", synced=True)
                session.add(offer)
                by_keitaro_id[missing_id] = offer
            if set(offer_ids) - {offer.keitaro_id for offer in offers}:
                await session.flush()

            links_by_offer_id = {link.offer_id: link for link in flow.offers}
            # What Keitaro-visible fields looked like before this update.
            # Keyed by the local Offer UUID: a binding created in this call has no
            # offer_id yet (it is only populated on flush), but always has link.offer.
            before = {link.offer.id: (link.share, link.state, link.deleted) for link in flow.offers}
            incoming_local_ids = set()
            for item in items:
                offer = by_keitaro_id[int(item["offer_id"])]
                incoming_local_ids.add(offer.id)
                link = links_by_offer_id.get(offer.id)
                if link is None:
                    # Assign the ORM relationship, not only offer_id. The service
                    # serializes link.offer after this repository session is closed.
                    link = FlowOffer(offer=offer, share=0)
                    flow.offers.append(link)
                    links_by_offer_id[offer.id] = link
                else:
                    # Keep the relationship explicitly populated for both existing
                    # and newly-created bindings before returning the detached Flow.
                    link.offer = offer
                state = item.get("state") or FlowOfferState.ACTIVE.value
                is_deleted = bool(item.get("deleted", False)) or state == "deleted"
                if state == "deleted":
                    # "deleted" is a legacy way to say deleted=True. It is not a real
                    # state, so keep the binding's own state (active/disabled) instead
                    # of silently turning a disabled offer into an active one.
                    current_state = link.state or FlowOfferState.ACTIVE
                    state = current_state.value
                if state not in {FlowOfferState.ACTIVE.value, FlowOfferState.DISABLED.value}:
                    raise ValueError(f"Invalid offer state: {state}")
                link.state = FlowOfferState(state)
                link.deleted = is_deleted
                link.share = 0 if link.deleted else int(item.get("share", 0))
                link.pinned = False if link.deleted else bool(item.get("pinned", False))

            # Bindings omitted from the submitted full list are retained as deleted.
            for link in flow.offers:
                if link.offer.id not in incoming_local_ids:
                    link.deleted = True
                    link.share = 0
                    link.pinned = False

            active_links = [link for link in links_by_offer_id.values() if not link.deleted]
            pinned_links = [link for link in active_links if link.pinned]
            unpinned_links = [link for link in active_links if not link.pinned]
            pinned_total = sum(link.share for link in pinned_links)
            if pinned_total > 100:
                raise ValueError("The total share of pinned offers cannot exceed 100%")
            remaining = 100 - pinned_total
            if not unpinned_links and active_links and remaining != 0:
                raise ValueError("All offers are pinned; their shares must total exactly 100%")
            if unpinned_links:
                base, remainder = divmod(remaining, len(unpinned_links))
                # Put remainder points on the last offers: 3 offers => 33, 33, 34.
                remainder_start = len(unpinned_links) - remainder
                for index, link in enumerate(unpinned_links):
                    link.share = base + (1 if index >= remainder_start else 0)

            # Mark as pending only what really differs from the pre-update state
            # (this also covers shares redistributed among unpinned offers).
            changed = False
            for link in flow.offers:
                previous = before.get(link.offer.id)
                if previous is None or previous != (link.share, link.state, link.deleted):
                    link.synced = False
                    changed = True
            if changed:
                flow.synced = False
            await session.flush()
            return flow

    async def get_flows_pending_sync(self) -> list[Flow]:
        """Fetch OFFER flows needing push sync to Keitaro.

        Returns flows where either Flow.synced=False or any FlowOffer.binding
        has synced=False. Excludes GEO flows and soft-deleted flows. Uses EXISTS
        subquery to find flows with dirty bindings without full JOINs.

        Args:
            None

        Returns:
            List of Flow entities with nested offers loaded for payload building.
        """
        async with self._session_factory() as session:
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
                .where(Flow.deleted.is_(False), Flow.type == FlowType.OFFER)
                .where(or_(Flow.synced.is_(False), dirty_link))
                .options(selectinload(Flow.offers).selectinload(FlowOffer.offer))
                .order_by(Flow.keitaro_id)
            )
            return list((await session.execute(query)).scalars().unique().all())

    async def mark_flow_synced(
        self,
        flow_id,
        pushed: dict[Any, tuple[int, str, bool]] | None = None,
    ) -> bool:
        """Mark a flow and its offer bindings as synced after a successful push.

        ``pushed`` is the snapshot that was actually sent to Keitaro:
        ``{FlowOffer.id: (share, state_value, deleted)}``. A binding is confirmed as
        synced only if it still has exactly these values. A binding edited (or created)
        while the PUT request was in flight stays ``synced=False`` and is picked up by
        the next push, instead of being marked as sent when it was not.

        The flow is marked synced only when none of its bindings remained pending.
        Without ``pushed`` every binding is confirmed (legacy behaviour).

        Args:
            flow_id: Local UUID of the flow that was pushed.
            pushed: Snapshot of the pushed bindings, keyed by FlowOffer.id.

        Returns:
            True if the flow is fully synced after this call, False if some bindings
            changed during the push and are still pending (or the flow no longer exists).
        """
        async with self._session_factory() as session, session.begin():
            flow = await session.scalar(
                select(Flow)
                .where(Flow.id == flow_id)
                .options(selectinload(Flow.offers))
                .with_for_update(of=Flow)
            )
            if flow is None:
                return False
            fully_synced = True
            for link in flow.offers:
                if pushed is not None and pushed.get(link.id) != (
                    link.share,
                    link.state.value,
                    link.deleted,
                ):
                    link.synced = False
                    fully_synced = False
                else:
                    link.synced = True
            flow.synced = fully_synced
            await session.flush()
            return fully_synced

    # ------------------------------------------------------------------ helpers

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
