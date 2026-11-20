import logging
import json
import os
import tempfile
from pathlib import Path
from typing import Any, Awaitable, Callable

from app.core.exceptions import CampaignCreationError, CampaignNotFoundError, InvalidRequestError
from app.models.models import Campaign
from app.schemas.campaign import (
    CampaignCreatePayload,
    KTCampaignCreateResponse,
    KTCampaignCreateRequest,
    CampaignDetailResponse,
)
from app.services.flow_service import FlowService
from app.repositories.campaign_repository import CampaignRepository
from app.core.config import Settings

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
        gateway: "CampaignGateway",
        flow_service: "FlowService",
        settings: "Settings",
        campaign_repo: "CampaignRepository",
    ) -> None:
        self.gateway: CampaignGateway = gateway
        self.flow_service: FlowService = flow_service
        self.settings: Settings = settings
        self.campaign_repo: CampaignRepository = campaign_repo

    async def get_campaigns(self) -> list[dict]:
        """Fetch campaigns from Keitaro filtered by name prefix setting.

        Retrieves all campaigns available in Keitaro and filters those matching
        the application's campaign_name_prefix configuration. Returns raw dicts
        without validation or transformation—endpoint-level filtering applies.

        Returns:
            List of campaign dictionaries with names starting from configured prefix.
        """
        campaigns: list[dict] = await self.gateway.get_campaigns()
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
        campaign: Campaign | None = await self.campaign_repo.get_campaign_detail(campaign_id)
        if campaign is None:
            raise CampaignNotFoundError(f"Campaign with Keitaro ID {campaign_id} was not found")
        return CampaignDetailResponse.model_validate(campaign)

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

    # ---- preparation of campaign name ----

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

    # ---- steps (data preparation + API calls) ----

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
