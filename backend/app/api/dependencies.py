from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends

from app.core.config import Settings, get_settings
from app.integrations.keitaro import KeitaroGateway


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
