from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends

from app.core.config import Settings, get_settings
from app.integrations.keitaro import KeitaroGateway
from app.integrations.flow_gateway import KeitaroFlowGateway
from app.integrations.campaign_gateway import KeitaroCampaignGateway
from app.services.campaign_service import CampaignService
from app.services.flow_service import FlowService


async def get_keitaro_gateway(
    settings: Annotated[Settings, Depends(get_settings)],
) -> AsyncGenerator[KeitaroGateway, None]:
    gateway = KeitaroGateway(
        base_url=settings.keitaro_base_url,
        api_key=settings.keitaro_api_token.get_secret_value(),
        timeout=settings.keitaro_timeout_seconds,
    )

    try:
        yield gateway
    finally:
        await gateway.close()


KeitaroDep = Annotated[
    KeitaroGateway,
    Depends(get_keitaro_gateway),
]


def get_flow_service(
    gateway: KeitaroDep,
) -> FlowService:
    flow_gateway = KeitaroFlowGateway(gateway)
    return FlowService(gateway=flow_gateway)


FlowServiceDep = Annotated[
    FlowService,
    Depends(get_flow_service),
]


def get_campaign_service(
    gateway: KeitaroDep,
    flow_service: FlowServiceDep,
) -> CampaignService:
    campaign_gateway = KeitaroCampaignGateway(gateway)

    return CampaignService(
        gateway=campaign_gateway,
        flow_service=flow_service,
    )


CampaignServiceDep = Annotated[
    CampaignService,
    Depends(get_campaign_service),
]
