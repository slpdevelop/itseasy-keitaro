from collections.abc import AsyncGenerator
from typing import Annotated

from app.services.campaign_service import CampaignService
from fastapi import Depends

from app.core.config import Settings, get_settings
from app.integrations.keitaro import KeitaroGateway
from app.integrations.campaign_gateway import KeitaroCampaignGateway


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


KeitaroDep = Annotated[KeitaroGateway, Depends(get_keitaro_gateway)]


def get_campaign_service(
    gateway: Annotated[
        KeitaroGateway,
        Depends(get_keitaro_gateway),
    ],
) -> CampaignService:
    campaign_gateway = KeitaroCampaignGateway(gateway)
    return CampaignService(campaign_gateway)


CampaignServiceDep = Annotated[
    CampaignService,
    Depends(get_campaign_service),
]
