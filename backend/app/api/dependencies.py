from typing import Annotated

import httpx
from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker

from app.core.config import Settings, get_settings
from app.integrations.keitaro import KeitaroGateway
from app.integrations.flow_gateway import KeitaroFlowGateway
from app.integrations.campaign_gateway import KeitaroCampaignGateway
from app.repositories.campaign_repository import CampaignRepository
from app.services.campaign_service import CampaignService
from app.services.flow_service import FlowService


def get_keitaro_gateway(request: Request) -> KeitaroGateway:
    client: httpx.AsyncClient = request.app.state.http_client
    return KeitaroGateway(client)


KeitaroDep = Annotated[KeitaroGateway, Depends(get_keitaro_gateway)]


def get_flow_service(gateway: KeitaroDep) -> FlowService:
    return FlowService(gateway=KeitaroFlowGateway(gateway))


FlowServiceDep = Annotated[FlowService, Depends(get_flow_service)]


def get_campaign_repository(request: Request) -> CampaignRepository:
    """Build the repository from the engine created in the app lifespan.

    The session factory is cached on app.state so one factory is shared by all requests.
    """
    state = request.app.state
    repository: CampaignRepository | None = getattr(state, "campaign_repository", None)
    if repository is None:
        engine: AsyncEngine = state.db_engine
        repository = CampaignRepository(async_sessionmaker(engine, expire_on_commit=False))
        state.campaign_repository = repository
    return repository


CampaignRepositoryDep = Annotated[CampaignRepository, Depends(get_campaign_repository)]


def get_campaign_service(
    gateway: KeitaroDep,
    flow_service: FlowServiceDep,
    settings: Annotated[Settings, Depends(get_settings)],
    campaign_repo: CampaignRepositoryDep,
) -> CampaignService:
    return CampaignService(
        gateway=KeitaroCampaignGateway(gateway),
        flow_service=flow_service,
        settings=settings,
        campaign_repo=campaign_repo,
    )


CampaignServiceDep = Annotated[CampaignService, Depends(get_campaign_service)]
