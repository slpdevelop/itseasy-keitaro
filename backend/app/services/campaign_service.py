import asyncio
import json
import logging
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Awaitable, Callable
from uuid import UUID

from pydantic import TypeAdapter, ValidationError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.config import Settings
from app.core.exceptions import (
    CampaignCreationError,
    CampaignNotFoundError,
    FlowNotFoundError,
    InvalidRequestError,
    KeitaroError,
)
from app.integrations.campaign_gateway import KeitaroCampaignGateway
from app.integrations.flow_gateway import KeitaroFlowGateway
from app.integrations.keitaro import KeitaroGateway
from app.models.models import Campaign, Flow, FlowOffer, FlowOfferState, FlowType, Offer
from app.repositories.campaign_repository import CampaignRepository
from app.repositories.flow_repository import FlowRepository
from app.repositories.offer_repository import OfferRepository
from app.schemas.campaign import (
    CampaignCreatePayload,
    CampaignDetailResponse,
    FlowPush,
    KTCampaignCreateRequest,
    KTCampaignCreateResponse,
    RemoteCampaign,
    SyncErrorStage,
    SyncResult,
)
from app.schemas.flow import FlowCreate, FlowFilter, RemoteFlow
from app.schemas.flow import FlowOffer as FlowOfferCreate
from app.schemas.offer import RemoteOffer

logger: logging.Logger = logging.getLogger(__name__)

OFFER_FETCH_CONCURRENCY: int = 10
REMOTE_FLOWS_ADAPTER: TypeAdapter[list[RemoteFlow]] = TypeAdapter(list[RemoteFlow])


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
    recovery from partial failures, pulls campaigns from Keitaro into the local
    database and pushes pending local offer changes back. Repositories are created
    per transaction from the injected session factory; Keitaro is accessed only
    through the campaign and flow gateways.

    Attributes:
        gateway: Shared KeitaroGateway for authenticated HTTP requests.
        campaign_gateway: Gateway for Keitaro campaigns API.
        flow_gateway: Gateway for Keitaro streams (flows) and offers API.
        settings: Application settings with campaign defaults (prefix, IDs).
        db_session: Session factory used to open one transaction per phase.
    """

    def __init__(
        self,
        gateway: "KeitaroGateway",
        settings: "Settings",
        db_session: "async_sessionmaker[AsyncSession]",
    ) -> None:
        self.gateway: KeitaroGateway = gateway
        self.campaign_gateway: KeitaroCampaignGateway = KeitaroCampaignGateway(gateway)
        self.flow_gateway: KeitaroFlowGateway = KeitaroFlowGateway(gateway)
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
        campaigns: list[dict] = await self.campaign_gateway.get_campaigns()
        return [
            campaign
            for campaign in campaigns
            if (campaign.get("name") or "").startswith(self.settings.campaign_name_prefix)
        ]

    async def get_campaign_detail(self, campaign_id: int) -> CampaignDetailResponse:
        """Retrieve full campaign details with flows and offer bindings.

        Reads the local projection by Keitaro ID and transforms it to the Pydantic
        response model. If the campaign is not stored locally yet, it is imported
        from Keitaro with fetch_campaign().

        Args:
            campaign_id: Numeric Keitaro ID of campaign to retrieve.

        Returns:
            CampaignDetailResponse with nested flows and offers.

        Raises:
            KeitaroError: If the campaign must be imported and Keitaro fails.
        """
        async with self.db_session() as session, session.begin():
            campaigns = CampaignRepository(session)
            campaign: Campaign | None = await campaigns.get_campaign_detail(campaign_id)
            if campaign is not None:
                return CampaignDetailResponse.model_validate(campaign)

        return await self.fetch_campaign(campaign_id)

    async def fetch_campaign(self, campaign_keitaro_id: int) -> CampaignDetailResponse:
        """Pull a campaign with its flows and offers from Keitaro into the local database.

        Pull sync, Keitaro is authoritative except for unpushed local edits:
        1. Network: load the campaign and its flows from Keitaro.
        2. Read: find offers referenced by flows that are not stored locally.
        3. Network: load details of the missing offers.
        4. Write: upsert campaign, create missing offers, reconcile flows and bindings
           in one transaction. Bindings with pending local changes (synced=False) are
           never overwritten, so a following sync_campaign() still pushes them.
        5. Read: build the response from the stored state.

        Args:
            campaign_keitaro_id: Numeric Keitaro ID of the campaign to fetch.

        Returns:
            CampaignDetailResponse with nested flows and offers.

        Raises:
            KeitaroError: If Keitaro fails or returns an invalid response.
            CampaignNotFoundError: If the campaign disappeared right after saving.
        """
        # 1. Network phase
        remote_campaign, remote_flows = await self._fetch_remote(campaign_keitaro_id)
        offer_ids: set[int] = self._get_remote_offer_ids(remote_flows)

        # 2. Read phase
        async with self.db_session() as session, session.begin():
            offers = OfferRepository(session)
            missing_offer_ids: set[int] = await offers.get_missing_keitaro_ids(offer_ids)

        # 3. Network phase
        missing_offers: list[RemoteOffer] = await self._fetch_missing_offers(missing_offer_ids)

        # 4. Write phase
        fetched_at: datetime = datetime.now(timezone.utc)
        async with self.db_session() as session, session.begin():
            campaigns = CampaignRepository(session)
            flows = FlowRepository(session)
            offers = OfferRepository(session)

            campaign: Campaign = await campaigns.create_or_update_campaign(
                remote_campaign, fetched_at=fetched_at
            )

            # Между фазами 2 и 4 параллельный запрос мог уже создать часть офферов.
            absent_ids: set[int] = await offers.get_missing_keitaro_ids(
                {offer.id for offer in missing_offers}
            )
            new_offers: list[RemoteOffer] = [o for o in missing_offers if o.id in absent_ids]
            if new_offers:
                await offers.bulk_create(new_offers, fetched_at=fetched_at)

            offers_by_kid: dict[int, Offer] = await offers.get_map_by_keitaro_ids(offer_ids)

            await self._reconcile_flows(flows, campaign, remote_flows, offers_by_kid, fetched_at)
            await flows.flush()

        # 5. Read phase
        async with self.db_session() as session, session.begin():
            campaigns = CampaignRepository(session)
            saved: Campaign | None = await campaigns.get_campaign_detail(campaign_keitaro_id)
            if saved is None:
                raise CampaignNotFoundError()
            return CampaignDetailResponse.model_validate(saved)

    async def _fetch_remote(self, keitaro_id: int) -> tuple[RemoteCampaign, list[RemoteFlow]]:
        """Load and validate a campaign and its flows from Keitaro.

        Raises:
            KeitaroError: If the response does not match the expected structure.
        """
        raw_campaign, raw_flows = await asyncio.gather(
            self.campaign_gateway.get_by_id(keitaro_id),
            self.flow_gateway.get_campaign_flows(keitaro_id),
        )
        try:
            remote_campaign = RemoteCampaign.model_validate(raw_campaign)
            remote_flows = REMOTE_FLOWS_ADAPTER.validate_python(raw_flows)
        except ValidationError as exc:
            logger.warning(
                "Invalid Keitaro response for campaign %s: %s",
                keitaro_id,
                exc.errors(include_input=False, include_url=False, include_context=False),
            )
            raise KeitaroError("Keitaro returned an invalid campaign or streams response") from exc
        return remote_campaign, remote_flows

    @staticmethod
    def _get_remote_offer_ids(remote_flows: list[RemoteFlow]) -> set[int]:
        """Collect Keitaro offer IDs referenced by the flows."""
        return {binding.offer_id for flow in remote_flows for binding in flow.offers}

    async def _fetch_missing_offers(self, offer_ids: set[int]) -> list[RemoteOffer]:
        """Load details of offers that are not stored locally.

        A failed request must neither cancel the others nor lose the binding that
        references the offer, so a placeholder named "Offer <id>" is returned for it
        (the same convention CampaignRepository uses for unknown offers).

        Args:
            offer_ids: Keitaro IDs of offers missing locally.

        Returns:
            One RemoteOffer per requested ID.
        """
        if not offer_ids:
            return []

        sem = asyncio.Semaphore(OFFER_FETCH_CONCURRENCY)

        async def _get_offer(offer_id: int) -> RemoteOffer:
            async with sem:
                try:
                    raw_offer = await self.flow_gateway.get_offer_details(offer_id)
                    return RemoteOffer.model_validate(raw_offer)
                except Exception:
                    logger.exception(
                        "Failed to fetch offer %s from Keitaro, storing a placeholder", offer_id
                    )
                    return RemoteOffer(id=offer_id, name=f"Offer {offer_id}")

        return list(await asyncio.gather(*(_get_offer(offer_id) for offer_id in offer_ids)))

    async def _reconcile_flows(
        self,
        flows: FlowRepository,
        campaign: Campaign,
        remote_flows: list[RemoteFlow],
        offers_by_kid: dict[int, Offer],
        fetched_at: datetime,
    ) -> None:
        """Make local flows of a campaign mirror Keitaro.

        Creates or updates every remote flow, reconciles its offer bindings and
        deletes local flows that no longer exist in Keitaro.
        """
        local_by_kid: dict[int, Flow] = {
            flow.keitaro_id: flow for flow in await flows.list_by_campaign(campaign.id)
        }
        remote_ids: set[int] = {remote.id for remote in remote_flows}

        for position, remote in enumerate(remote_flows):
            flow: Flow | None = local_by_kid.get(remote.id)
            if flow is None:
                flow = Flow(keitaro_id=remote.id, campaign_id=campaign.id, offers=[])
                flows.add(flow)

            flow.type = FlowType.OFFER if remote.offers else FlowType.GEO
            flow.name = remote.name or flow.type.value
            flow.position = position
            flow.schema = remote.schema_
            flow.action_type = remote.action_type
            flow.action_payload = remote.action_payload
            if remote.country is not None:
                flow.country = remote.country
            flow.fetched_at = fetched_at
            flow.deleted = False

            self._reconcile_offers(flow, remote, offers_by_kid)

            # Флоу остаётся "pending", пока у любой привязки есть непушнутая правка.
            flow.synced = not any(binding.synced is False for binding in flow.offers)

        for keitaro_id, flow in local_by_kid.items():
            if keitaro_id not in remote_ids:
                await flows.delete(flow=flow)

    def _reconcile_offers(
        self, flow: Flow, remote: RemoteFlow, offers_by_kid: dict[int, Offer]
    ) -> None:
        """Make offer bindings of a flow mirror Keitaro without losing local edits.

        Bindings with pending local changes (synced=False) win over the remote copy:
        a pending binding equal to Keitaro is confirmed, a different one is kept and
        pushed later by sync_campaign(). Bindings absent in Keitaro are soft-deleted.
        """
        bindings_by_offer_id: dict[UUID, FlowOffer] = {b.offer_id: b for b in flow.offers}
        seen_offer_ids: set[UUID] = set()

        for remote_binding in remote.offers:
            # в ответе Keitaro: id привязки != offer_id
            offer: Offer | None = offers_by_kid.get(remote_binding.offer_id)
            if offer is None:
                logger.warning(
                    "Offer %s from flow %s not found locally, skipping",
                    remote_binding.offer_id,
                    remote.id,
                )
                continue
            seen_offer_ids.add(offer.id)
            state = FlowOfferState(remote_binding.state)

            binding: FlowOffer | None = bindings_by_offer_id.get(offer.id)
            if binding is None:
                binding = FlowOffer(
                    offer=offer,
                    share=remote_binding.share,
                    state=state,
                    synced=True,
                    deleted=False,
                )
                flow.offers.append(binding)
                bindings_by_offer_id[offer.id] = binding  # защита от дублей
            elif binding.synced is False:
                if (binding.deleted, binding.share, binding.state) == (
                    False,
                    remote_binding.share,
                    state,
                ):
                    binding.synced = True  # локальная правка совпала с Keitaro
                else:
                    logger.warning(
                        "Pending local binding of offer %s in flow %s kept over Keitaro copy",
                        remote_binding.offer_id,
                        remote.id,
                    )
            else:
                binding.share = remote_binding.share
                binding.state = state
                binding.synced = True
                binding.deleted = False

        for binding in flow.offers:
            # offer_id пуст только у новых привязок: они уже в seen_offer_ids
            if binding.offer_id is None or binding.offer_id in seen_offer_ids:
                continue
            if binding.synced is False:
                if binding.deleted:
                    binding.synced = True  # локальное удаление уже совпадает с Keitaro
                else:
                    logger.warning(
                        "Pending local binding %s is absent in Keitaro flow %s, kept",
                        binding.id,
                        remote.id,
                    )
                continue
            binding.deleted = True
            binding.share = 0
            binding.pinned = False
            binding.synced = True

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
        response = await self.campaign_gateway.create_campaign(payload)
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
        geo_code = country_code.strip().upper()
        geo_flow_data = FlowCreate(
            campaign_id=campaign_id,
            name=f"Geo {geo_code} -> Google",
            action_payload="https://google.com",
            schema="redirect",
            filters=[FlowFilter(name="country", mode="accept", payload=[geo_code])],
        )
        return await self.flow_gateway.create_flow(geo_flow_data)

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
        if not offer_id_list:
            raise InvalidRequestError("At least one offer is required to create an offer stream")
        base, remainder = divmod(100, len(offer_id_list))
        remainder_start = len(offer_id_list) - remainder
        offers = [
            FlowOfferCreate(
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
        return await self.flow_gateway.create_flow(offer_flow_data)

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

    async def sync_campaign(self, campaign_keitaro_id: int) -> SyncResult:
        """Push pending local offer bindings of one campaign's OFFER flows to Keitaro.

        Push sync, one flow at a time so a single failure never blocks the others:
        1. Read: find the campaign, load its flows with unpushed changes and build
           immutable FlowPush snapshots inside the session; flows with an invalid
           payload are reported.
        2. Network: send the flow's offers to Keitaro.
        3. Write: confirm exactly the pushed bindings. Bindings edited meanwhile stay
           pending and are reported in flows_still_pending.

        Args:
            campaign_keitaro_id: Numeric Keitaro ID of the campaign to sync.

        Returns:
            SyncResult with counters, flows left pending, flows deleted meanwhile
            and per-flow errors with the stage they happened at.

        Raises:
            CampaignNotFoundError: If the campaign is not stored locally.
        """
        # 1. Read phase
        async with self.db_session() as session, session.begin():
            campaigns = CampaignRepository(session)
            campaign: Campaign | None = await campaigns.get_by_keitaro_id(campaign_keitaro_id)
            if campaign is None:
                raise CampaignNotFoundError()
            flows: list[Flow] = await campaigns.get_flows_pending_sync(campaign.id)
            pending: list[FlowPush] = []
            invalid: list[tuple[int, ValidationError]] = []
            for flow in flows:
                try:
                    pending.append(FlowPush.from_flow(flow))
                except ValidationError as exc:
                    invalid.append((flow.keitaro_id, exc))

        result = SyncResult(campaign_id=campaign_keitaro_id, flows_checked=len(flows))

        for keitaro_id, exc in invalid:
            logger.warning(
                "Flow %s skipped, invalid payload: %s",
                keitaro_id,
                exc.errors(include_input=False, include_url=False, include_context=False),
            )
            result.add_error(keitaro_id, SyncErrorStage.VALIDATION, exc)

        for item in pending:
            # 2. Network phase
            try:
                await self.flow_gateway.update_flow_offers(item.keitaro_id, item.offers)
            except Exception as exc:
                logger.exception("Keitaro push failed for flow %s", item.keitaro_id)
                result.add_error(item.keitaro_id, SyncErrorStage.PUSH, exc)
                continue

            # 3. Write phase
            try:
                async with self.db_session() as session, session.begin():
                    campaigns = CampaignRepository(session)
                    confirmed: bool = await campaigns.mark_flow_synced(
                        item.flow_id, item.pushed_fingerprints
                    )
            except FlowNotFoundError:
                logger.warning("Flow %s was deleted before the push was confirmed", item.keitaro_id)
                result.flows_not_found.append(item.keitaro_id)
                continue
            except Exception as exc:
                logger.exception(
                    "Pushed flow %s to Keitaro but failed to mark it synced", item.keitaro_id
                )
                result.add_error(item.keitaro_id, SyncErrorStage.MARK_SYNCED, exc)
                continue

            if confirmed:
                result.flows_synced += 1
            else:
                result.flows_still_pending.append(item.keitaro_id)

        return result
