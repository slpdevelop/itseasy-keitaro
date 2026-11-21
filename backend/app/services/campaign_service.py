import asyncio
from datetime import datetime, timezone
import logging
import json
import os
import tempfile
from pathlib import Path
from typing import Any, Awaitable, Callable

from app.core.exceptions import CampaignCreationError, CampaignNotFoundError, InvalidRequestError
from app.models.models import Campaign, Offer
from app.schemas.campaign import (
    CampaignCreatePayload,
    KTCampaignCreateResponse,
    KTCampaignCreateRequest,
    CampaignDetailResponse,
)
from app.services.flow_service import FlowService
from app.repositories.campaign_repository import CampaignRepository
from app.core.config import Settings
from app.integrations.campaign_gateway import KeitaroCampaignGateway
from app.integrations.flow_gateway import KeitaroFlowGateway
from app.integrations.keitaro import KeitaroGateway
from app.repositories.offer_repository import OfferRepository
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

logger: logging.Logger = logging.getLogger(__name__)


class Checkpoint:
    """Checkpoint manager for multi-step async operations.

    Persists completed step results to disk between requests, enabling resume
    from the last successful step after failures or restarts. Used by
    CampaignService.create_campaign() to handle partial failures safely.

    Storage location is fixed (not mkdtemp) so concurrent creation attempts can
    read each other's checkpoints for idempotency protection.

    Attributes:
        path: Filepath to JSON checkpoint storage file.
        key: Operation name (e.g., campaign name) used as prefix in data dict.
    """

    DEFAULT_PATH = Path(tempfile.gettempdir()) / "campaign_checkpoint.json"

    def __init__(self, key: str, path=None):
        self.path: Path = Path(path) if path else self.DEFAULT_PATH
        self.key: str = key

    def _read(self) -> dict:
        """Read checkpoint data from file."""
        return json.loads(self.path.read_text("utf-8")) if self.path.exists() else {}

    def _write(self, data: dict) -> None:
        """Atomically write checkpoint data to file using temp rename."""
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp: Path = self.path.with_suffix(".tmp")
        tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), "utf-8")
        os.replace(tmp, self.path)

    async def run(self, step: str, fn: Callable[[], Awaitable[Any]]) -> Any:
        """Execute an asynchronous step, skipping if already completed.

        Checks checkpoint for prior success; if found, returns cached result.
        Otherwise executes the function and saves result to checkpoint before
        returning. Exception causes immediate propagation without partial save.

        Args:
            step: Step name stored in checkpoint (unique within key).
            fn: Async callable that performs the operation.

        Returns:
            Result of the operation or cached checkpoint value.

        Raises:
            Any exception raised by fn, logged as warning before re-raising.
        """
        done = self._read().get(self.key, {})
        if step in done:
            return done[step]

        try:
            result = await fn()
        except Exception:
            logger.warning("Step %r failed for %r; next request resumes from it", step, self.key)
            raise

        data: dict = self._read()
        data.setdefault(self.key, {})[step] = result
        self._write(data)
        return result

    def clear(self) -> None:
        """Remove checkpoint for a key to restart operation from scratch."""
        data: dict = self._read()
        if data.pop(self.key, None) is not None:
            self._write(data)


class CampaignService:
    """Business logic for campaign creation and lifecycle operations.

    Orchestrates multi-step campaign creation in Keitaro with checkpoint-based
    recovery from partial failures. Creates campaigns, GEO flows, and OFFER flows
    while persisting local projections to database. Uses dependency injection
    pattern with CampaignGateway and FlowService for testability.

    Attributes:
        gateway: CampaignGateway for HTTP requests to Keitaro campaigns API.
        flow_service: FlowService for creating flows and binding offers.
        settings: Application settings with campaign defaults (prefix, IDs).
        campaign_repo: Repository for persisting local campaign data.
    """

    def __init__(
        self,
        gateway: "KeitaroGateway",
        settings: "Settings",
        db_session: "async_sessionmaker[AsyncSession]",
    ) -> None:
        self.gateway: KeitaroGateway = gateway
        self.settings: Settings = settings
        self.db_session: "async_sessionmaker[AsyncSession]" = db_session

    async def get_campaigns(self) -> list[dict]:
        """Fetch campaigns from Keitaro filtered by name prefix setting.

        Retrieves all campaigns available in Keitaro and filters those matching
        the application's campaign_name_prefix configuration. Returns raw dicts
        without validation or transformation—endpoint-level filtering applies.

        Returns:
            List of campaign dictionaries with names starting from configured prefix.
        """
        gateway = KeitaroCampaignGateway(self.gateway)
        campaigns: list[dict] = await gateway.get_campaigns()
        return [
            campaign
            for campaign in campaigns
            if (campaign.get("name") or "").startswith(self.settings.campaign_name_prefix)
        ]

    async def get_campaign_detail(self, campaign_id: int) -> CampaignDetailResponse:
        """Retrieve full campaign details with flows and offer bindings.

        Fetches complete campaign entity from repository by Keitaro ID, validates
        existence, and transforms to Pydantic response model. Raises CampaignNotFoundError
        if no local projection exists for the specified ID.

        Args:
            campaign_id: Numeric Keitaro ID of campaign to retrieve.

        Returns:
            CampaignDetailResponse with nested flows and offers.

        Raises:
            CampaignNotFoundError: If campaign not found locally.
        """
        campaign_repository = CampaignRepository(session_factory=self.db_session)
        campaign: Campaign | None = await campaign_repository.get_campaign_detail(campaign_id)
        if campaign is None:
            keitaro_campaign: dict | None = await self.gateway.get_by_id(campaign_id)
            campaign = campaign_repository.create_campaign(keitaro_campaign)

        return campaign

    async def fetch_campaign(self, campaign_keitaro_id: int) -> Campaign:
        """Fetch a campaign and fully reconcile its flows and offer bindings."""
        from sqlalchemy import select
        from sqlalchemy.orm import selectinload
        from app.models.models import Flow, FlowOffer, FlowOfferState, FlowType

        campaign_gateway = KeitaroCampaignGateway(self.gateway)
        flow_gateway = KeitaroFlowGateway(self.gateway)

        remote_campaign = await campaign_gateway.get_by_id(campaign_keitaro_id)
        remote_flows = await flow_gateway.get_campaign_flows(campaign_keitaro_id)
        if isinstance(remote_flows, dict):
            remote_flows = remote_flows.get("streams", remote_flows.get("items", remote_flows.get("data", [])))
        if not isinstance(remote_flows, list):
            raise InvalidRequestError("Keitaro returned an invalid campaign streams response")

        fetched_at = datetime.now(timezone.utc)
        async with self.db_session() as session, session.begin():
            campaign_result = await session.execute(
                select(Campaign)
                .where(Campaign.keitaro_id == campaign_keitaro_id)
                .options(selectinload(Campaign.flows).selectinload(Flow.offers))
            )
            campaign = campaign_result.scalar_one_or_none()
            if campaign is None:
                campaign = Campaign(keitaro_id=campaign_keitaro_id)
                session.add(campaign)

            campaign.name = remote_campaign["name"]
            campaign.domain_keitaro_id = remote_campaign.get("domain_id")
            campaign.group_keitaro_id = remote_campaign.get("group_id")
            campaign.traffic_source_keitaro_id = remote_campaign.get("traffic_source_id")
            campaign.fetched_at = fetched_at
            await session.flush()

            # Reconcile flows by their Keitaro IDs. Missing remote flows are
            # physically deleted; Flow.offers uses delete-orphan cascade.
            remote_flow_ids = set()
            local_flows_result = await session.execute(
                select(Flow).where(Flow.campaign_id == campaign.id)
                .options(selectinload(Flow.offers).selectinload(FlowOffer.offer))
            )
            local_flows = local_flows_result.scalars().unique().all()
            local_by_kid = {flow.keitaro_id: flow for flow in local_flows}
            remote_by_kid = {}

            for position, remote in enumerate(remote_flows, start=1):
                if not isinstance(remote, dict) or not isinstance(remote.get("id"), int):
                    continue
                flow_kid = remote["id"]
                remote_flow_ids.add(flow_kid)
                remote_by_kid[flow_kid] = remote
                flow = local_by_kid.get(flow_kid)
                if flow is None:
                    flow = Flow(keitaro_id=flow_kid, campaign_id=campaign.id)
                    session.add(flow)

                schema = remote.get("schema")
                remote_offers = remote.get("offers") or []
                flow_type = FlowType.OFFER if schema == "landings" or remote_offers else FlowType.GEO
                country = None
                for filter_item in remote.get("filters") or []:
                    if filter_item.get("name") == "country":
                        payload = filter_item.get("payload") or []
                        country = payload[0] if payload else None
                        break

                flow.name = remote.get("name") or ""
                flow.type = flow_type
                flow.position = remote.get("position", position)
                flow.schema = schema
                flow.action_type = remote.get("action_type")
                flow.action_payload = remote.get("action_payload")
                flow.country = country
                flow.fetched_at = fetched_at
                flow.synced = True
                flow.deleted = False

            for flow in local_flows:
                if flow.keitaro_id not in remote_flow_ids:
                    await session.delete(flow)

            await session.flush()

            # The Offer rows are assumed to have been refreshed already. The API
            # offer_id identifies the Offer; the API offer.id identifies only
            # the association and must not be used as the Offer key.
            offer_kids = {
                item.get("offer_id")
                for remote in remote_flows
                if isinstance(remote, dict)
                for item in (remote.get("offers") or [])
                if isinstance(item, dict) and isinstance(item.get("offer_id"), int)
            }
            offers_result = await session.execute(
                select(Offer).where(Offer.keitaro_id.in_(offer_kids)) if offer_kids
                else select(Offer).where(False)
            )
            offers_by_kid = {offer.keitaro_id: offer for offer in offers_result.scalars().all()}

            for flow_kid, remote in remote_by_kid.items():
                flow = local_by_kid.get(flow_kid)
                if flow is None:
                    flow_result = await session.execute(
                        select(Flow).where(Flow.keitaro_id == flow_kid)
                    )
                    flow = flow_result.scalar_one()
                remote_bindings = remote.get("offers") or []
                remote_offer_kids = set()

                for remote_binding in remote_bindings:
                    if not isinstance(remote_binding, dict):
                        continue
                    offer_kid = remote_binding.get("offer_id")
                    offer = offers_by_kid.get(offer_kid)
                    if offer is None:
                        continue
                    remote_offer_kids.add(offer_kid)
                    binding = next(
                        (item for item in flow.offers if item.offer_id == offer.id), None
                    )
                    state_value = remote_binding.get("state") or "active"
                    state = FlowOfferState(state_value)
                    if binding is None:
                        binding = FlowOffer(
                            flow_id=flow.id,
                            offer_id=offer.id,
                            share=remote_binding.get("share", 0),
                            state=state,
                            synced=True,
                            deleted=False,
                        )
                        session.add(binding)
                    else:
                        binding.share = remote_binding.get("share", 0)
                        binding.state = state
                        binding.synced = True
                        binding.deleted = False

                for binding in flow.offers:
                    if binding.offer.keitaro_id not in remote_offer_kids:
                        binding.deleted = True

                flow.synced = True

            await session.flush()
            return campaign

    async def _sync_flows(
        self,
        *,
        campaign,
        remote_flows,
        refs_by_flow,
        local_offers_by_kid,
        fetched_at,
        flow_repo,
        flow_offer_repo,
    ) -> None:
        # 1. Потоки целиком зеркалим из API (insert / update / восстановление deleted)
        flow_upserts = [
            FlowUpsert(
                campaign_id=campaign.id,
                keitaro_id=rf.keitaro_id,
                name=rf.name,
                type=rf.type,
                position=position,
                schema=rf.schema,
                action_type=rf.action_type,
                action_payload=rf.action_payload,
                country=rf.country,
                fetched_at=fetched_at,
                synced=True,
                deleted=False,
            )
            for position, rf in enumerate(remote_flows)
        ]
        local_flows = await flow_repo.bulk_upsert_by_keitaro_id(
            flow_upserts
        )  # dict[keitaro_id, Flow]

        # 2. Потоки, которых нет в API, удалены в Keitaro (UI потоки не меняет, конфликтов нет)
        await flow_repo.mark_deleted_except(
            campaign_id=campaign.id,
            keep_keitaro_ids=set(local_flows),
            synced=True,
        )
        # Все привязки пропавших потоков закрываем, включая ожидающие добавления из UI:
        # отправлять их некуда
        await flow_offer_repo.mark_deleted_by_flows_except(
            campaign_id=campaign.id,
            keep_flow_ids={f.id for f in local_flows.values()},
            synced=True,
        )

        # 3. Офферы синхронизируем только у OFFER-потоков (у GEO их нет)
        for rf in remote_flows:
            if rf.type != FlowType.OFFER:
                continue
            await self._sync_flow_offers(
                flow=local_flows[rf.keitaro_id],
                remote_refs=refs_by_flow.get(rf.keitaro_id, []),
                local_offers_by_kid=local_offers_by_kid,
                flow_offer_repo=flow_offer_repo,
            )

    async def _sync_flow_offers(
        self,
        *,
        flow,
        remote_refs,
        local_offers_by_kid,
        flow_offer_repo,
    ) -> None:
        # Включая deleted: из-за UniqueConstraint(flow_id, offer_id) tombstone
        # нужно воскрешать, а не вставлять новую строку. offer подгружен (joinedload).
        local_bindings = await flow_offer_repo.list_by_flow(flow.id, include_deleted=True)
        local_by_offer_kid = {b.offer.keitaro_id: b for b in local_bindings}

        remote_offer_kids: set[int] = set()
        to_upsert: list[FlowOfferUpsert] = []

        # --- A. Привязки из API: перезаписываем и восстанавливаем ---
        for ref in remote_refs:
            local_offer = local_offers_by_kid.get(ref.offer_keitaro_id)
            if local_offer is None:
                # оффер упомянут в потоке, но полного объекта в Keitaro нет
                logger.warning(
                    "Offer %s referenced by flow %s not found",
                    ref.offer_keitaro_id,
                    flow.keitaro_id,
                )
                continue  # в remote_offer_kids не попадает -> обработается в блоке B

            remote_offer_kids.add(ref.offer_keitaro_id)
            existing = local_by_offer_kid.get(ref.offer_keitaro_id)
            to_upsert.append(
                FlowOfferUpsert(
                    id=existing.id if existing else None,
                    flow_id=flow.id,
                    offer_id=local_offer.id,
                    share=ref.share,  # API приоритетнее, даже при локальном synced=False
                    state=ref.state,
                    pinned=existing.pinned if existing else False,  # чисто локальное поле
                    synced=True,
                    deleted=False,  # восстановление локально удалённых
                )
            )
        await flow_offer_repo.bulk_upsert(to_upsert)

        # --- B. Локальные привязки, которых нет в API ---
        for offer_kid, binding in local_by_offer_kid.items():
            if offer_kid in remote_offer_kids:
                continue

            if binding.deleted:
                # удаление фактически применено (или в Keitaro оффера и не было)
                if not binding.synced:
                    await flow_offer_repo.mark_synced(binding.id)
            elif binding.synced:
                # был синхронизирован, а в Keitaro пропал -> удалён там
                await flow_offer_repo.mark_deleted(binding.id, synced=True)
            # else: synced=False, deleted=False -> ожидающее добавление из UI, не трогаем

    async def create_campaign(self, data: KTCampaignCreateRequest) -> KTCampaignCreateResponse:
        """Create campaign in Keitaro with GEO and OFFER flows using checkpoint recovery.

        Multi-step operation protected by Checkpoint mechanism:
        1. Create campaign in Keitaro (save ID to checkpoint)
        2. Create GEO flow for geographic targeting (save result)
        3. Create OFFER flow with offer bindings (save result)
        4. Save all entities to local database

        If any step fails, subsequent steps are skipped and checkpoint allows
        retry from last successful operation on next request.

        Args:
            data: Request with name, country_code, and list of Keitaro offer IDs.

        Returns:
            KTCampaignCreateResponse with campaign ID and confirmation message.
        """
        campaign_name = self._build_campaign_name(data.name)
        cp = Checkpoint(key=campaign_name)

        campaign_id = await cp.run(
            "create_campaign",
            lambda: self._create_campaign_in_keitaro(campaign_name),
        )
        geo_flow = await cp.run(
            "create_geo_flow",
            lambda: self._create_geo_flow(campaign_id, data.country_code),
        )
        offer_flow = await cp.run(
            "create_offer_flow",
            lambda: self._create_offer_flow(campaign_id, data.offer_id_list),
        )
        await cp.run(
            "save_to_db",
            lambda: self._save_campaign_to_db(
                campaign_id, campaign_name, data.country_code, geo_flow, offer_flow
            ),
        )

        return KTCampaignCreateResponse(
            campaign_id=campaign_id,
            campaign_name=campaign_name,
            message="Campaign and flows successfully created",
        )

    def _build_campaign_name(self, raw_name: str) -> str:
        """Prefix user-provided name with config setting and validate length.

        Applies application's campaign_name_prefix to ensure consistent naming
        in Keitaro system. Trims whitespace from input and rejects names
        exceeding 255-character Keitaro limit.

        Args:
            raw_name: User-provided campaign name.

        Returns:
            Complete campaign name with prefix applied.

        Raises:
            InvalidRequestError: If final name exceeds 255 characters.
        """
        name = raw_name
        if not name.startswith(self.settings.campaign_name_prefix):
            name = f"{self.settings.campaign_name_prefix}{name}"
        if len(name) > 255:
            raise InvalidRequestError("Campaign name exceeds the 255-character Keitaro limit")
        return name

    async def _create_campaign_in_keitaro(self, campaign_name: str) -> int:
        """Create new campaign in Keitaro using application defaults.

        Builds CampaignCreatePayload from settings (domain/group/traffic source IDs)
        and sends POST request to Keitaro campaigns endpoint. Validates response ID
        is valid integer > 0; raises error if not.

        Args:
            campaign_name: Full name to register in Keitaro (with prefix).

        Returns:
            Numeric campaign ID returned by Keitaro API.

        Raises:
            CampaignCreationError: If invalid or missing campaign ID in response.
        """
        payload = CampaignCreatePayload(
            name=campaign_name,
            domain_id=self.settings.campaign_domain_id,
            group_id=self.settings.campaign_group_id,
            traffic_source_id=self.settings.campaign_traffic_source_id,
            state="active",
        )
        response = await self.gateway.create_campaign(payload)
        campaign_id = response.get("id") if isinstance(response, dict) else None
        if not isinstance(campaign_id, int) or campaign_id <= 0:
            raise CampaignCreationError("Keitaro did not return a valid campaign id")
        return campaign_id

    async def _create_geo_flow(self, campaign_id: int, country_code: str) -> dict:
        """Create GEO flow for geographic targeting within campaign.

        Delegates to FlowService.create_geo_flow() which builds FlowCreate payload
        with country filter and returns created flow data. Result saved to checkpoint
        for database persistence later.

        Args:
            campaign_id: Parent campaign Keitaro ID.
            country_code: ISO 2-letter code for geographic targeting.

        Returns:
            Dictionary containing GEO flow details from Keitaro API.
        """
        return await self.flow_service.create_geo_flow(campaign_id, country_code)

    async def _create_offer_flow(self, campaign_id: int, offer_id_list: list[int]) -> dict:
        """Create OFFER flow with specified offer bindings within campaign.

        Delegates to FlowService.create_offer_flow() which calculates equal
        traffic share per offer and returns created flow data. Saved to checkpoint.

        Args:
            campaign_id: Parent campaign Keitaro ID.
            offer_id_list: List of Keitaro offer IDs to bind to flow.

        Returns:
            Dictionary containing OFFER flow details from Keitaro API.
        """
        return await self.flow_service.create_offer_flow(campaign_id, offer_id_list)

    async def _save_campaign_to_db(
        self,
        campaign_id: int,
        campaign_name: str,
        country_code: str,
        geo_flow: dict,
        offer_flow: dict,
    ) -> None:
        """Persist new campaign and flows to local database.

        Atomically saves campaign entity, GEO flow data, OFFER flow data, and all
        offer bindings using CampaignRepository.save_created_campaign(). Marks flows
        as synced after successful persistence.

        Args:
            campaign_id: Numeric Keitaro ID of created campaign.
            campaign_name: Display name to store locally.
            country_code: Country code for GEO flow targeting.
            geo_flow: Complete GEO flow dictionary from Keitaro response.
            offer_flow: OFFER flow dictionary with nested offer bindings.
        """
        await self.campaign_repo.save_created_campaign(
            keitaro_id=campaign_id,
            name=campaign_name,
            domain_keitaro_id=self.settings.campaign_domain_id,
            group_keitaro_id=self.settings.campaign_group_id,
            traffic_source_keitaro_id=self.settings.campaign_traffic_source_id,
            country_code=country_code,
            geo_flow=geo_flow,
            offer_flow=offer_flow,
        )
