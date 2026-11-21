from typing import Annotated

import httpx
from fastapi import Depends, Request

from app.integrations.keitaro_api import KeitaroAPI
from app.core.config import Settings, get_settings
from app.integrations.keitaro_gateway import KeitaroGateway
from app.services.service import Service


def get_keitaro_api(request: Request) -> KeitaroAPI:
    """Provide a Keitaro API client built on the shared HTTP client.

    Args:
        request: FastAPI request object containing app state.

    Returns:
        KeitaroAPI that reuses the application-wide httpx client.
    """
    client: httpx.AsyncClient = request.app.state.http_client
    gateway = KeitaroGateway(client)
    return KeitaroAPI(gateway)


KeitaroAPIDep = Annotated[KeitaroAPI, Depends(get_keitaro_api)]


def get_service(
    api: KeitaroAPIDep, settings: Annotated[Settings, Depends(get_settings)], request: Request
) -> Service:
    """Create and inject Service with all required dependencies.

    Args:
        api: Keitaro API client for upstream calls.
        settings: Application settings with campaign defaults.
        request: Request, used to reach the shared database session factory.

    Returns:
        Configured Service instance ready for campaign operations.
    """

    return Service(
        api=api,
        settings=settings,
        session_factory=request.app.state.session_factory,
    )


ServiceDep = Annotated[Service, Depends(get_service)]
