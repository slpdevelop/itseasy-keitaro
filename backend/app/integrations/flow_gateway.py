import logging
from typing import Any

from app.integrations.keitaro import KeitaroGateway
from app.schemas.campaign import OfferPayload
from app.schemas.flow import FlowCreate

logger: logging.Logger = logging.getLogger(__name__)


class KeitaroFlowGateway:
    """Gateway for stream/flow operations in Keitaro.

    Wraps the main KeitaroGateway to handle flow-specific paths and payloads.
    Used to create, retrieve, and update campaign flows (streams) with their
    associated configurations. Only offers can be modified on existing flows.

    Args:
        gateway: Parent KeitaroGateway instance for HTTP communication.

    Methods are async to support non-blocking I/O during API calls.
    """

    def __init__(self, gateway: KeitaroGateway) -> None:
        """Initialize FlowGateway with parent HTTP gateway.

        Args:
            gateway: KeitaroGateway for making authenticated requests.
        """
        self.gateway: KeitaroGateway = gateway

    async def create_flow(self, data: FlowCreate) -> dict:
        """Create a new flow/stream for a campaign.

        Sends flow configuration (type, position, schema/action, country, etc.)
        to Keitaro and returns the created flow details. Payload is serialized
        with aliases preserved and None values excluded.

        Args:
            data: FlowCreate schema with complete flow configuration.

        Returns:
            Dictionary containing created flow metadata from Keitaro.
        """
        return await self.gateway.post(
            "/streams", data.model_dump(exclude_none=True, by_alias=True)
        )

    async def get_campaign_flows(self, campaign_id: int) -> Any:
        """Retrieve all flows/streams for a specific campaign.

        Fetches GEO and OFFER flows associated with a campaign from Keitaro.
        Response includes flow IDs, types, positions, and current offer bindings.

        Args:
            campaign_id: Numeric ID of the campaign whose flows to retrieve.

        Returns:
            List of flow dictionaries or raw response data.
        """
        return await self.gateway.get(f"/campaigns/{campaign_id}/streams")

    async def update_flow_offers(self, flow_id: int, offers: list[OfferPayload]) -> Any:
        """Update offer bindings for an existing flow without changing other settings.

        Sends only the offers field to Keitaro's PUT endpoint, preserving all
        other flow configuration (filters, rules, schema, actions). Useful for
        synchronizing FlowOffer entities without affecting upstream stream logic.

        Args:
            flow_id: Numeric ID of the flow whose offers to update.
            offers: List of OfferPayload with offer_id, share (0-100), and state.

        Returns:
            Updated flow data or raw response from Keitaro.
        """
        return await self.gateway.put(
            f"/streams/{flow_id}", {"offers": [offer.model_dump() for offer in offers]}
        )

    async def get_offer_details(self, offer_id: int) -> Any:
        """Retrieve an offer from Keitaro to resolve its display name during sync."""
        return await self.gateway.get(f"/offers/{offer_id}")
