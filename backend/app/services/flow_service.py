from typing import Any

from app.api.dependencies import KeitaroFlowGateway
from app.core.exceptions import InvalidRequestError
from app.repositories.campaign_repository import CampaignRepository


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

    async def update_flow_offers(self, flow_id, offers: list[dict[str, Any]]) -> dict[str, Any]:
        """Update local offer bindings for a flow and return normalized state."""
        if len({item.get("offer_id") for item in offers}) != len(offers):
            raise InvalidRequestError("An offer cannot be added to the same flow more than once")
        for item in offers:
            if not isinstance(item.get("offer_id"), int) or item["offer_id"] <= 0:
                raise InvalidRequestError("Invalid Keitaro offer ID")
            state = item.get("state", "active")
            if state not in {"active", "disabled", "deleted"}:
                raise InvalidRequestError("Offer state must be 'active', 'disabled' or 'deleted'")
            if state == "deleted" and not item.get("deleted", False):
                raise InvalidRequestError("Deleted state requires deleted=true")
        try:
            flow = await self.repository.update_flow_offers(flow_id, offers)
        except ValueError as exc:
            raise InvalidRequestError(str(exc)) from exc
        if flow is None:
            from app.core.exceptions import FlowNotFoundError

            raise FlowNotFoundError()
        return {
            "success": True,
            "flow_id": str(flow.id),
            "offers": [
                {
                    "offer_id": link.offer.keitaro_id,
                    "share": link.share,
                    "pinned": link.pinned,
                    "state": link.state.value,
                    "deleted": link.deleted,
                    "synced": link.synced,
                }
                for link in flow.offers
            ],
        }

    async def sync_to_keitaro(self) -> dict[str, Any]:
        """Push all pending offer binding changes to Keitaro flows.

        Finds OFFER flows where Flow.synced=False or any FlowOffer.binding has synced=False.
        For each pending flow, builds offers payload excluding deleted bindings, sends PUT request,
        then confirms as synced exactly the bindings that were sent. Bindings edited while the
        request was in flight stay pending and the flow is listed in ``flows_still_pending``.
        Aggregates errors but continues processing.

        Returns statistics: flows_checked, flows_synced count, flows_still_pending list,
        errors list, success flag.

        Args:
            None (queries repository for dirty flows)

        Returns:
            Dictionary with sync progress and error tracking.
        """
        flows = await self.repository.get_flows_pending_sync()
        result: dict[str, Any] = {
            "flows_checked": len(flows),
            "flows_synced": 0,
            "flows_still_pending": [],
            "errors": [],
        }

        for flow in flows:
            # Snapshot of exactly what is sent, so only these values get confirmed.
            pushed = {link.id: (link.share, link.state.value, link.deleted) for link in flow.offers}
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
                if await self.repository.mark_flow_synced(flow.id, pushed):
                    result["flows_synced"] += 1
                else:
                    result["flows_still_pending"].append(flow.keitaro_id)
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

    async def get_campaign_flows(self, campaign_id: int) -> list[dict]:
        return await self.gateway.get_campaign_flows(campaign_id=campaign_id)
