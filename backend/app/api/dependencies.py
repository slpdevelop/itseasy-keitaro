from typing import Annotated

import httpx
from fastapi import Depends, Request

from app.core.config import Settings, get_settings
from app.integrations.keitaro_gateway import KeitaroGateway
from app.services.campaign_service import CampaignService
from app.services.offer_service import OfferService


def get_keitaro_gateway(request: Request) -> KeitaroGateway:
    """Provide shared Keitaro HTTP client gateway for all requests.

    Retrieves the singleton httpx.AsyncClient from app.state and wraps it with
    KeitaroGateway to handle API authentication, timeouts, and error responses.
    Do not create separate clients in services or endpoints - use this dependency.

    Args:
        request: FastAPI request object containing app state.

    Returns:
        Configured KeitaroGateway instance with the shared HTTP client.
    """
    client: httpx.AsyncClient = request.app.state.http_client
    return KeitaroGateway(client)


KeitaroDep = Annotated[KeitaroGateway, Depends(get_keitaro_gateway)]


def get_campaign_service(
    gateway: KeitaroDep, settings: Annotated[Settings, Depends(get_settings)], request: Request
) -> CampaignService:
    """Create and inject CampaignService with all required dependencies.

    Orchestrates multi-step campaign creation by combining gateway adapters for
    upstream communication, repository for persistence, and application settings
    for default campaign configuration (name prefix, group ID, domain ID, etc.).

    Args:
        gateway: KeitaroGateway for HTTP requests to create campaigns.
        flow_service: FlowService for creating flows and binding offers.
        settings: Application settings with campaign defaults and database config.
        campaign_repo: Repository for saving campaign entities locally.

    Returns:
        Configured CampaignService instance ready for campaign operations.
    """

    return CampaignService(
        gateway=gateway,
        settings=settings,
        db_session=request.app.state.session_factory,
    )


CampaignServiceDep = Annotated[CampaignService, Depends(get_campaign_service)]


def get_offer_service(gateway: KeitaroDep, request: Request) -> OfferService:
    """Build an offer service using the application's shared session factory."""
    return OfferService(gateway=gateway, db_session=request.app.state.session_factory)


OfferServiceDep = Annotated[OfferService, Depends(get_offer_service)]
