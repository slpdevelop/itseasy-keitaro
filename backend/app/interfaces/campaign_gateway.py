from typing import Protocol

from app.schemas.campaign import CampaignCreate
from app.schemas.offer import OfferResponse


class CampaignGateway(Protocol):

    async def create_campaign(
        self,
        data: CampaignCreate,
    ) -> dict: ...

    async def delete_campaign(
        self,
        campaign_id: int,
    ) -> None: ...

    async def get_offers(self) -> list[OfferResponse]: ...

    async def get_campaign_offers(
        self,
        campaign_id: int,
    ) -> list[OfferResponse]: ...

    async def add_offers(
        self,
        campaign_id: int,
        offer_ids: list[int],
    ) -> list[int]: ...

    async def remove_offers(
        self,
        campaign_id: int,
        offer_ids: list[int],
    ) -> list[int]: ...
