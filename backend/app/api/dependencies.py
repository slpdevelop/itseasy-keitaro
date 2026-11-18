from typing import Annotated

import httpx
from fastapi import Depends, Request

from app.core.config import Settings, get_settings
from app.integrations.keitaro import KeitaroGateway
from app.integrations.flow_gateway import KeitaroFlowGateway
from app.integrations.campaign_gateway import KeitaroCampaignGateway
from app.services.campaign_service import CampaignService
from app.services.flow_service import FlowService


def get_keitaro_gateway(request: Request) -> KeitaroGateway:
    client: httpx.AsyncClient = request.app.state.http_client
    return KeitaroGateway(client)


KeitaroDep = Annotated[KeitaroGateway, Depends(get_keitaro_gateway)]


def get_flow_service(gateway: KeitaroDep) -> FlowService:
    return FlowService(gateway=KeitaroFlowGateway(gateway))


FlowServiceDep = Annotated[FlowService, Depends(get_flow_service)]


def get_campaign_service(
    gateway: KeitaroDep,
    flow_service: FlowServiceDep,
    settings: Annotated[Settings, Depends(get_settings)],
) -> CampaignService:
    return CampaignService(
        gateway=KeitaroCampaignGateway(gateway),
        flow_service=flow_service,
        settings=settings,
    )


CampaignServiceDep = Annotated[CampaignService, Depends(get_campaign_service)]
