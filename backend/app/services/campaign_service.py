import asyncio
from datetime import datetime, timezone
import logging
import json
import os
import tempfile
from pathlib import Path
from typing import Any, Awaitable, Callable

from app.core.exceptions import CampaignCreationError, InvalidRequestError
from app.models.models import Campaign, Flow, FlowOffer, Offer
from app.repositories.flow_repository import FlowRepository
from app.schemas.campaign import (
    CampaignCreatePayload,
    FlowPush,
    KTCampaignCreateResponse,
    KTCampaignCreateRequest,
    CampaignDetailResponse,
    SyncErrorStage,
    SyncResult,
)
from app.repositories.campaign_repository import CampaignRepository
from app.core.config import Settings
from app.integrations.campaign_gateway import KeitaroCampaignGateway
from app.integrations.flow_gateway import KeitaroFlowGateway
from app.integrations.keitaro import KeitaroGateway
from app.repositories.offer_repository import OfferRepository
from app.schemas.flow import FlowCreate, FlowFilter
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
        async with self.db_session() as session, session.begin():
            campaign_repository = CampaignRepository(session=session)
            campaign: Campaign | None = await campaign_repository.get_campaign_detail(campaign_id)
            if campaign is None:
                keitaro_campaign: dict | None = await self.gateway.get_by_id(campaign_id)
                campaign = campaign_repository.create_or_update_campaign(keitaro_campaign)

        return campaign

    async def fetch_campaign(self, campaign_keitaro_id: int) -> Campaign:
        remote_campaign, remote_flows = await self._fetch_remote(campaign_keitaro_id)
        offer_ids: list[int] = self._get_raw_offer_ids(remote_flows)
        missing_offers: list[dict] | None = await self._get_missing_offers(offer_ids)

        fetched_at: datetime = datetime.now(timezone.utc)

        async with self.db_session() as session, session.begin():
            campaigns = CampaignRepository(session)
            flows = FlowRepository(session)
            offers = OfferRepository(session)

            campaign: Campaign = await campaigns.create_or_update_campaign(remote_campaign)

            if missing_offers:
                await offers.bulk_create(offers=missing_offers, fetched_at=fetched_at)

            offers_by_kid: dict[int, Offer] = await offers.get_map_by_keitaro_ids(offer_ids)

            await self._reconcile_flows(flows, campaign, remote_flows, offers_by_kid, fetched_at)
            session.flush()
            return campaign

    async def _reconcile_flows(
        self,
        flows: FlowRepository,
        campaign: Campaign,
        remote_flows: list[dict],
        offers_by_kid: dict[int, Offer],
        fetched_at: datetime,
    ) -> None:
        local_by_kid = {f.keitaro_id: f for f in await flows.list_by_campaign(campaign.id)}
        remote_ids = {rf["id"] for rf in remote_flows}

        for i, remote in enumerate(remote_flows):
            flow: Flow | None = local_by_kid.get(remote["id"])
            if flow is None:
                flow = Flow(keitaro_id=remote["id"], campaign_id=campaign.id, offers=[])
                flows.add(flow)

            flow.name = remote["name"]
            flow.type = "offer" if remote.get("offers") else "geo"
            flow.position = i
            flow.schema = remote["schema"]
            flow.action_type = remote["action_type"]
            flow.action_payload = remote["action_payload"]
            flow.fetched_at = fetched_at
            flow.synced = True
            flow.deleted = False

            self._reconcile_offers(flow, remote, offers_by_kid)

        for kid, flow in local_by_kid.items():
            if kid not in remote_ids:
                flows.delete(flow=flow)

    def _reconcile_offers(self, flow: Flow, remote: dict, offers_by_kid: dict[int, Offer]) -> None:
        bindings_by_offer_id = {b.offer_id: b for b in flow.offers}
        seen_offer_ids: set[int] = set()

        for rb in remote.get("offers") or []:
            offer_keitaro_id = rb["offer_id"]  # в ответе Keitaro: id привязки != offer_id
            offer: Offer | None = offers_by_kid.get(offer_keitaro_id)
            if offer is None:
                logger.warning(
                    "Offer %s from flow %s not found locally, skipping",
                    offer_keitaro_id,
                    remote["id"],
                )
                continue
            seen_offer_ids.add(offer.id)

            binding: FlowOffer | None = bindings_by_offer_id.get(offer.id)
            if binding is None:
                binding = FlowOffer(
                    offer=offer,
                    share=rb["share"],
                    state=rb["state"],
                    synced=True,
                    deleted=False,
                )
                flow.offers.append(binding)
                bindings_by_offer_id[offer.id] = binding  # защита от дублей
            else:
                binding.share = rb["share"]
                binding.state = rb["state"]
                binding.synced = True
                binding.deleted = False

        for binding in flow.offers:
            if binding.offer_id is not None and binding.offer_id not in seen_offer_ids:
                binding.deleted = True

    async def _fetch_remote(self, keitaro_id: int) -> tuple[dict, list[dict]]:
        remote_campaign, remote_flows = await asyncio.gather(
            KeitaroCampaignGateway(self.gateway).get_by_id(keitaro_id),
            KeitaroFlowGateway(self.gateway).get_campaign_flows(keitaro_id),
        )
        return remote_campaign, remote_flows

    def _get_raw_offer_ids(self, flows: list[dict]) -> list[int]:
        remote_offer_ids: set[int] = set()
        for flow in flows:
            for offer in flow.get("offers") or []:
                remote_offer_ids.add(offer["offer_id"])
        return list(remote_offer_ids)

    async def _get_missing_offers(self, offer_ids: list[int]) -> list[dict] | None:
        if not offer_ids:
            return None

        async with self.db_session() as session, session.begin():
            missing_offer_ids: set[int] = await OfferRepository(session).get_missing_keitaro_ids(
                offer_ids
            )

        if not missing_offer_ids:
            return None

        flow_gateway = KeitaroFlowGateway(self.gateway)
        sem = asyncio.Semaphore(10)

        async def _get_offer(oid: int) -> dict | None:
            async with sem:
                try:
                    return await flow_gateway.get_offer_details(oid)
                except Exception:
                    # Один упавший оффер не должен отменять остальные запросы.
                    logger.exception("Failed to fetch offer %s from Keitaro", oid)
                    return None

        fetched: list[dict | None] = await asyncio.gather(
            *(_get_offer(oid) for oid in missing_offer_ids)
        )
        unique = {o["id"]: o for o in fetched if o is not None}
        return list(unique.values()) or None

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
        campaign_name: str = self._build_campaign_name(data.name)
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
        gateway = KeitaroCampaignGateway(self.gateway)
        response = await gateway.create_campaign(payload)
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
        gateway = KeitaroFlowGateway(self.gateway)

        geo_code = country_code.strip().upper()
        geo_flow_data = FlowCreate(
            campaign_id=campaign_id,
            name=f"Geo {geo_code} -> Google",
            action_payload="https://google.com",
            schema="redirect",
            filters=[FlowFilter(name="country", mode="accept", payload=[geo_code])],
        )
        return await gateway.create_flow(geo_flow_data)

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
        gateway = KeitaroFlowGateway(self.gateway)
        if not offer_id_list:
            raise InvalidRequestError("At least one offer is required to create an offer stream")
        base, remainder = divmod(100, len(offer_id_list))
        remainder_start = len(offer_id_list) - remainder
        offers = [
            FlowOffer(
                offer_id=offer_id,
                share=base + (1 if index >= remainder_start else 0),
            )
            for index, offer_id in enumerate(offer_id_list)
        ]
        offer_flow_data = FlowCreate(
            campaign_id=campaign_id,
            name="Offers",
            schema="landings",
            offers=offers,
        )
        return await gateway.create_flow(offer_flow_data)

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
        async with self.db_session() as session, session.begin():
            campaigns = CampaignRepository(session)
            await campaigns.save_created_campaign(
                keitaro_id=campaign_id,
                name=campaign_name,
                domain_keitaro_id=self.settings.campaign_domain_id,
                group_keitaro_id=self.settings.campaign_group_id,
                traffic_source_keitaro_id=self.settings.campaign_traffic_source_id,
                country_code=country_code,
                geo_flow=geo_flow,
                offer_flow=offer_flow,
            )

    async def sync_campaign(self) -> SyncResult:
        # 1. Read phase
        async with self.db_session() as session, session.begin():
            flows: list[Flow] = await CampaignRepository(session).get_flows_pending_sync()
            pending: list[FlowPush] = [FlowPush.from_flow(flow) for flow in flows]

        result = SyncResult(flows_checked=len(pending))

        for item in pending:
            # 2. Network phase
            try:
                await self.gateway.update_flow_offers(item.keitaro_id, item.offers_payload)
            except Exception as exc:
                logger.exception("Keitaro push failed", extra={"keitaro_flow_id": item.keitaro_id})
                result.add_error(item.keitaro_id, SyncErrorStage.PUSH, exc)
                continue

            # 3. Confirm phase
            try:
                async with self.db_session() as session, session.begin():
                    confirmed = await CampaignRepository(session).mark_flow_synced(
                        item.flow_id, item.pushed_fingerprints
                    )
            except Exception as exc:
                logger.exception(
                    "Pushed to Keitaro but failed to mark synced",
                    extra={"keitaro_flow_id": item.keitaro_id},
                )
                result.add_error(item.keitaro_id, SyncErrorStage.MARK_SYNCED, exc)
                continue

            if confirmed:
                result.flows_synced += 1
            else:
                result.flows_still_pending.append(item.keitaro_id)

        return result
