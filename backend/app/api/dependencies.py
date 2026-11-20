from typing import Annotated

import httpx
from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker

from app.core.config import Settings, get_settings
from app.integrations.keitaro import KeitaroGateway
from app.integrations.flow_gateway import KeitaroFlowGateway
from app.integrations.campaign_gateway import KeitaroCampaignGateway
from app.repositories.campaign_repository import CampaignRepository
from app.repositories.offer_repository import OfferRepository
from app.services.campaign_service import CampaignService
from app.services.flow_service import FlowService
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


def get_campaign_repository(request: Request) -> CampaignRepository:
    """Provide shared CampaignRepository instance for the application lifetime.

    Lazily creates and caches a single repository instance using the app's database
    engine. Subsequent calls reuse the same repository with the same session factory,
    ensuring consistent transaction handling across endpoints.

    Args:
        request: FastAPI request object containing app state.

    Returns:
        Cached CampaignRepository instance sharing the same async session factory.
    """
    state = request.app.state
    repository: CampaignRepository | None = getattr(state, "campaign_repository", None)
    if repository is None:
        engine: AsyncEngine = state.db_engine
        repository = CampaignRepository(async_sessionmaker(engine, expire_on_commit=False))
        state.campaign_repository = repository
    return repository


CampaignRepositoryDep = Annotated[CampaignRepository, Depends(get_campaign_repository)]


def get_flow_service(gateway: KeitaroDep, repository: CampaignRepositoryDep) -> FlowService:
    """Create and inject FlowService with campaign gateway and repository.

    Orchestrates flow-to-stream operations by combining the KeitaroGateway adapter
    for upstream communication and the repository for local data persistence.
    Uses KeitaroFlowGateway to interact with flows/streams API endpoints.

    Args:
        gateway: KeitaroGateway for HTTP requests (injected from dependency).
        repository: CampaignRepository for saving flow entities locally.

    Returns:
        Configured FlowService instance ready for business operations.
    """
    return FlowService(gateway=KeitaroFlowGateway(gateway), repository=repository)


FlowServiceDep = Annotated[FlowService, Depends(get_flow_service)]


def get_campaign_service(
    gateway: KeitaroDep,
    flow_service: FlowServiceDep,
    settings: Annotated[Settings, Depends(get_settings)],
    campaign_repo: CampaignRepositoryDep,
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
        gateway=KeitaroCampaignGateway(gateway),
        flow_service=flow_service,
        settings=settings,
        campaign_repo=campaign_repo,
    )


CampaignServiceDep = Annotated[CampaignService, Depends(get_campaign_service)]


def get_offer_repository(request: Request) -> OfferRepository:
    """Provide shared OfferRepository instance for the application lifetime.

    Lazily creates and caches a single repository instance using the app's database
    engine. Reuses the same session factory as CampaignRepository to maintain
    consistent transaction handling across offer-related endpoints.

    Args:
        request: FastAPI request object containing app state.

    Returns:
        Cached OfferRepository instance sharing the same async session factory.
    """
    state = request.app.state
    repository: OfferRepository | None = getattr(state, "offer_repository", None)
    if repository is None:
        engine: AsyncEngine = state.db_engine
        repository = OfferRepository(async_sessionmaker(engine, expire_on_commit=False))
        state.offer_repository = repository
    return repository


OfferRepositoryDep = Annotated[OfferRepository, Depends(get_offer_repository)]


def get_offer_service(gateway: KeitaroDep, repository: OfferRepositoryDep) -> OfferService:
    """Create and inject OfferService with offer gateway and repository.

    Orchestrates offer import/sync operations by combining the gateway for fetching
    offers from Keitaro and the repository for local data persistence and soft-delete
    management of offer entities.

    Args:
        gateway: KeitaroGateway or Offer-specific gateway for HTTP requests.
        repository: OfferRepository for saving/restoring offers locally.

    Returns:
        Configured OfferService instance ready for offer operations.
    """
    return OfferService(gateway=gateway, repository=repository)


OfferServiceDep = Annotated[OfferService, Depends(get_offer_service)]
