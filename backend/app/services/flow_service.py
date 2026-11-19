from typing import Any

from app.core.exceptions import InvalidRequestError
from app.interfaces.flow_gateway import FlowGateway
from app.repositories.campaign_repository import CampaignRepository
from app.schemas.flow import FlowFilter, FlowCreate, FlowOffer


class FlowService:
    def __init__(self, gateway: FlowGateway, repository: CampaignRepository):
        self.gateway: FlowGateway = gateway
        self.repository = repository

    async def create_geo_flow(self, campaign_id: int, geo_code: str) -> dict:
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
        """Pull offer bindings for locally tracked campaigns from Keitaro."""
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
            except Exception as exc:  # one unavailable campaign must not stop other campaigns
                result["errors"].append(
                    {"campaign_id": campaign_id, "error": type(exc).__name__}
                )
                continue

            local_flow_ids = {flow["keitaro_id"] for flow in campaign["flows"]}
            for remote_flow in remote_flows:
                flow_id = remote_flow.get("id")
                if flow_id not in local_flow_ids or "offers" not in remote_flow:
                    continue
                try:
                    items = self._validate_remote_offers(remote_flow["offers"])
                    synced = await self.repository.sync_flow_offers_from_keitaro(
                        flow_id, items
                    )
                    if synced:
                        result["flows_synced"] += 1
                except Exception as exc:
                    result["errors"].append(
                        {"campaign_id": campaign_id, "flow_id": flow_id, "error": type(exc).__name__}
                    )
        result["success"] = not result["errors"]
        return result

    async def sync_to_keitaro(self) -> dict[str, Any]:
        """Push all pending offer bindings, one complete offers collection per flow."""
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
                result["errors"].append(
                    {"flow_id": flow.keitaro_id, "error": type(exc).__name__}
                )

        result["success"] = not result["errors"]
        return result

    @staticmethod
    def _extract_flows(response: Any) -> list[dict[str, Any]]:
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
