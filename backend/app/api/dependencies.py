from typing import Annotated

import httpx
from fastapi import Depends, Request

from app.integrations.keitaro_api import KeitaroAPI
from app.core.config import Settings, get_settings
from app.integrations.keitaro_gateway import KeitaroGateway
from app.services.service import Service


def get_keitaro_api(request: Request) -> KeitaroAPI:
    """Provide shared Keitaro API .

    Args:
        request: FastAPI request object containing app state.

    Returns:
        Configured KeitaroGateway instance with the shared HTTP client.
    """
    client: httpx.AsyncClient = request.app.state.http_client
    gateway = KeitaroGateway(client)
    return KeitaroAPI(gateway)


KeitaroAPIDep = Annotated[KeitaroAPI, Depends(get_keitaro_api)]


def get_service(
    api: KeitaroAPIDep, settings: Annotated[Settings, Depends(get_settings)], request: Request
) -> Service:
    """Create and inject Service with all required dependencies.

    Orchestrates multi-step campaign creation by combining gateway adapters for
    upstream communication, repository for persistence, and application settings
    for default campaign configuration (name prefix, group ID, domain ID, etc.).

    Args:
        gateway: KeitaroGateway for HTTP requests to create campaigns.
        flow_service: FlowService for creating flows and binding offers.
        settings: Application settings with campaign defaults and database config.
        campaign_repo: Repository for saving campaign entities locally.

    Returns:
        Configured Service instance ready for campaign operations.
    """

    return Service(
        api=api,
        settings=settings,
        session_factory=request.app.state.session_factory,
    )


ServiceDep = Annotated[Service, Depends(get_service)]
