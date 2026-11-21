from typing import TYPE_CHECKING, Any

from app.schemas.campaign import CampaignCreatePayload

if TYPE_CHECKING:
    from app.integrations.keitaro_gateway import KeitaroGateway
    from app.schemas.campaign import OfferPayload
    from app.schemas.flow import FlowCreate


class KeitaroAPI:
    """Keitaro Admin API client: campaigns, flows (streams) and offers.

    Wraps KeitaroGateway with one method per Keitaro endpoint we use. Used by
    Service. Payloads are serialized with exclude_none for clean requests.

    Args:
        gateway: Parent KeitaroGateway instance for HTTP communication.

    All methods are async for non-blocking I/O during API calls.
    """

    def __init__(self, gateway: "KeitaroGateway") -> None:
        """Initialize the API client with the HTTP gateway.

        Args:
            gateway: KeitaroGateway for making authenticated requests.
        """
        self.gateway: KeitaroGateway = gateway

    async def get_campaigns(self) -> list[dict]:
        """Fetch all campaigns from Keitaro with application name prefix filter.

        Retrieves the complete list of campaigns available in Keitaro. The parent
        service applies filtering by campaign_name_prefix before returning results.

        Returns:
            List of campaign dictionaries from Keitaro API response.
        """
        return await self.gateway.get("/campaigns")

    async def create_campaign(self, data: CampaignCreatePayload) -> dict:
        """Create a new campaign in Keitaro with specified configuration.

        Sends campaign creation payload (name, alias, domain_id, group_id, etc.)
        to the /campaigns endpoint. Payload is serialized excluding None values.

        Args:
            data: CampaignCreatePayload with name, group_id, domain_id, traffic_source_id.

        Returns:
            Keitaro response containing created campaign metadata (id, name).
        """
        return await self.gateway.post("/campaigns", data.model_dump(exclude_none=True))

    async def get_campaign_by_id(self, campaign_id: int) -> dict:
        """Fetch a single campaign's details from Keitaro by ID.

        Retrieves complete campaign configuration for the specified numeric ID.
        Returns raw dictionary from Keitaro response (not filtered or transformed).

        Args:
            campaign_id: Numeric ID of the campaign to retrieve.

        Returns:
            Campaign details dictionary from Keitaro API.
        """
        return await self.gateway.get(f"/campaigns/{campaign_id}")

    async def create_flow(self, data: "FlowCreate") -> dict:
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

    async def update_flow_offers(self, flow_id: int, offers: list["OfferPayload"]) -> Any:
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

    async def get_keitaro_offers(self) -> Any:
        """Fetch complete offer catalog from Keitaro API.

        Retrieves all active offers available in Keitaro system for potential
        import into local database or display in UI offer selection interfaces.

        Returns:
            Raw response from Keitaro /offers endpoint (structure varies by API version).
        """
        return await self.gateway.get("/offers")
