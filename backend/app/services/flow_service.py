from typing import Any

from app.api.dependencies import KeitaroFlowGateway
from app.core.exceptions import InvalidRequestError
from app.repositories.campaign_repository import CampaignRepository
from app.schemas.flow import FlowFilter, FlowCreate, FlowOffer


class FlowService:
    """Business logic for flow/stream creation and synchronization.

    Orchestrates operations on campaign flows (streams) including:
    - Creation of GEO flows for geographic targeting
    - Creation of OFFER flows with traffic distribution
    - Pull sync from Keitaro (offer bindings into local DB)
    - Push sync to Keitaro (local changes to upstream)

    Uses dependency injection with KeitaroFlowGateway for API calls and
    CampaignRepository for local persistence operations.

    Attributes:
        gateway: KeitaroFlowGateway for HTTP requests to streams/flows API.
        repository: CampaignRepository for flow entity persistence.
    """

    def __init__(self, gateway: KeitaroFlowGateway, repository: CampaignRepository):
        self.gateway: KeitaroFlowGateway = gateway
        self.repository = repository

    async def create_geo_flow(self, campaign_id: int, geo_code: str) -> dict:
        """Create GEO flow for geographic targeting with Google redirect.

        Builds FlowCreate payload with country filter pointing to Google search.
        Returns created flow details from Keitaro API for use in checkpoint and DB save.

        Args:
            campaign_id: Parent campaign numeric ID in Keitaro.
            geo_code: ISO 2-letter country code for targeting (e.g., "US", "RU").

        Returns:
            Dictionary containing created GEO flow data from Keitaro response.
        """
        geo_code = geo_code.strip().upper()
        geo_flow_data = FlowCreate(
            campaign_id=campaign_id,
            name=f"Geo {geo_code} -> Google",
            action_payload="https://google.com",
            schema="redirect",
            filters=[FlowFilter(name="country", mode="accept", payload=[geo_code])],
        )
        return await self.gateway.create_flow(geo_flow_data)

    async def create_offer_flow(self, campaign_id: int, offer_ids: list[int]) -> dict:
        """Create OFFER flow with equal traffic share across specified offers.

        Validates that at least one offer is provided, calculates 100/num_offers
        as share percentage, builds FlowCreate with offers array, and returns created flow.

        Args:
            campaign_id: Parent campaign numeric ID in Keitaro.
            offer_ids: List of Keitaro offer IDs to bind (min 1 required).

        Returns:
            Dictionary containing created OFFER flow data from Keitaro response.

        Raises:
            InvalidRequestError: If empty offer list provided.
        """
        if not offer_ids:
            raise InvalidRequestError("At least one offer is required to create an offer stream")
        share = int(100 / len(offer_ids))
        offers = [FlowOffer(offer_id=offer_id, share=share) for offer_id in offer_ids]
        offer_flow_data = FlowCreate(
            campaign_id=campaign_id,
            name="Offers",
            schema="landings",
            offers=offers,
        )
        return await self.gateway.create_flow(offer_flow_data)

    async def sync_from_keitaro(self) -> dict[str, Any]:
        """Pull offer bindings for tracked campaigns from Keitaro API.

        Iterates over locally tracked campaigns and their flows, fetches current
        offer collections from Keitaro, validates incoming data format, then
        replaces local FlowOffer entities with authoritative remote values.
        Creates Offer stubs for offers not yet imported.

        Returns statistics: campaigns_checked, flows_synced count, errors list, success flag.

        Args:
            None (uses locally tracked campaigns from repository)

        Returns:
            Dictionary with sync progress and error tracking.
        """
        campaigns = await self.repository.get_local_campaign_streams()
        result: dict[str, Any] = {
            "campaigns_checked": len(campaigns),
            "flows_synced": 0,
            "errors": [],
        }

        for campaign in campaigns:
            campaign_id = campaign["keitaro_id"]
            try:
                remote_flows = self._extract_flows(
                    await self.gateway.get_campaign_flows(campaign_id)
                )
            except Exception as exc:
                result["errors"].append({"campaign_id": campaign_id, "error": type(exc).__name__})
                continue

            local_flow_ids = {flow["keitaro_id"] for flow in campaign["flows"]}
            for remote_flow in remote_flows:
                flow_id = remote_flow.get("id")
                if flow_id not in local_flow_ids or "offers" not in remote_flow:
                    continue
                try:
                    items = self._validate_remote_offers(remote_flow["offers"])
                    synced = await self.repository.sync_flow_offers_from_keitaro(flow_id, items)
                    if synced:
                        result["flows_synced"] += 1
                except Exception as exc:
                    result["errors"].append(
                        {
                            "campaign_id": campaign_id,
                            "flow_id": flow_id,
                            "error": type(exc).__name__,
                        }
                    )
        result["success"] = not result["errors"]
        return result

    async def sync_to_keitaro(self) -> dict[str, Any]:
        """Push all pending offer binding changes to Keitaro flows.

        Finds OFFER flows where Flow.synced=False or any FlowOffer.binding has synced=False.
        For each pending flow, builds offers payload excluding deleted bindings, sends PUT request,
        then marks flow and all its bindings as synced. Aggregates errors but continues processing.

        Returns statistics: flows_checked, flows_synced count, errors list, success flag.

        Args:
            None (queries repository for dirty flows)

        Returns:
            Dictionary with sync progress and error tracking.
        """
        flows = await self.repository.get_flows_pending_sync()
        result: dict[str, Any] = {
            "flows_checked": len(flows),
            "flows_synced": 0,
            "errors": [],
        }

        for flow in flows:
            offers = [
                {
                    "offer_id": link.offer.keitaro_id,
                    "share": link.share,
                    "state": link.state.value,
                }
                for link in flow.offers
                if not link.deleted
            ]
            try:
                await self.gateway.update_flow_offers(flow.keitaro_id, offers)
                await self.repository.mark_flow_synced(flow.id)
                result["flows_synced"] += 1
            except Exception as exc:
                result["errors"].append({"flow_id": flow.keitaro_id, "error": type(exc).__name__})

        result["success"] = not result["errors"]
        return result

    @staticmethod
    def _extract_flows(response: Any) -> list[dict[str, Any]]:
        """Extract flows/streams from various Keitaro API response formats.

        Handles different possible response structures (list, dict with streams/items/data keys).
        Validates extracted data is array of dicts; raises error if format mismatch.

        Args:
            response: Raw API response object to parse.

        Returns:
            List of flow dictionaries from response.

        Raises:
            InvalidRequestError: If response structure invalid or flows not found.
        """
        if isinstance(response, list):
            flows = response
        elif isinstance(response, dict):
            flows = response.get("streams", response.get("items", response.get("data")))
        else:
            flows = None
        if not isinstance(flows, list) or any(not isinstance(item, dict) for item in flows):
            raise InvalidRequestError("Keitaro returned an invalid campaign streams response")
        return flows

    @staticmethod
    def _validate_remote_offers(items: Any) -> list[dict[str, Any]]:
        """Validate and extract offer bindings from Keitaro stream response.

        Checks each item in offers array has valid numeric ID (int > 0), share (0-100),
        and state ("active" or "disabled"). Returns cleaned list for repository processing.

        Args:
            items: Array of offer dicts from Keitaro stream response.

        Returns:
            Validated list of offer dictionaries with offer_id, share, state keys.

        Raises:
            InvalidRequestError: If any item fails validation checks.
        """
        if not isinstance(items, list):
            raise InvalidRequestError("Keitaro returned an invalid stream offers collection")
        validated = []
        for item in items:
            if not isinstance(item, dict):
                raise InvalidRequestError("Keitaro returned an invalid stream offer")
            offer_id = item.get("offer_id")
            share = item.get("share")
            state = item.get("state") or "active"
            if not isinstance(offer_id, int) or offer_id <= 0:
                raise InvalidRequestError("Keitaro returned an invalid offer ID in a stream")
            if not isinstance(share, int) or not 0 <= share <= 100:
                raise InvalidRequestError("Keitaro returned an invalid offer share in a stream")
            if state not in {"active", "disabled"}:
                raise InvalidRequestError("Keitaro returned an invalid offer state in a stream")
            validated.append({"offer_id": offer_id, "share": share, "state": state})
        return validated
