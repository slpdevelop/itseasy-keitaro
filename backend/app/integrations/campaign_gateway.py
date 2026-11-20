from typing import TYPE_CHECKING

from app.schemas.campaign import CampaignCreatePayload

if TYPE_CHECKING:
    from app.integrations.keitaro import KeitaroGateway


class KeitaroCampaignGateway:
    """Gateway for campaign CRUD operations in Keitaro.

    Wraps the parent KeitaroGateway to handle campaign-specific API endpoints.
    Used by CampaignService for creating, fetching, and deleting campaigns.
    Handles serialization of campaign payloads with exclude_none for clean requests.

    Args:
        gateway: Parent KeitaroGateway instance for HTTP communication.

    All methods are async for non-blocking I/O during API calls.
    """

    def __init__(self, gateway: "KeitaroGateway") -> None:
        """Initialize CampaignGateway with parent HTTP gateway.

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

    async def delete_campaign(self, campaign_id: int) -> None:
        """Delete a campaign from Keitaro by numeric ID.

        Sends DELETE request to soft-delete or remove the specified campaign.
        Expected to return HTTP 204 No Content on success.

        Args:
            campaign_id: Numeric ID of the campaign to delete.

        Returns:
            None after successful deletion.
        """
        await self.gateway.delete(f"/campaigns/{campaign_id}")

    async def get_by_id(self, campaign_id: int) -> dict:
        """Fetch a single campaign's details from Keitaro by ID.

        Retrieves complete campaign configuration for the specified numeric ID.
        Returns raw dictionary from Keitaro response (not filtered or transformed).

        Args:
            campaign_id: Numeric ID of the campaign to retrieve.

        Returns:
            Campaign details dictionary from Keitaro API.

        Note:
            Original code had incorrect return type annotation; this fixes it.
        """
        return await self.gateway.get(f"/campaigns/{campaign_id}")
