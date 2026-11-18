from app.interfaces.flow_gateway import FlowGateway
from app.schemas.flow import FlowFilter, FlowCreate, FlowOffer


class FlowService:

    def __init__(self, gateway: FlowGateway):
        self.gateway: FlowGateway = gateway

    async def create_geo_flow(self, campaign_id: int, geo_code: str) -> dict:

        geo_code = geo_code.strip().upper()

        geo_flow_data = FlowCreate(
            campaign_id=campaign_id,
            name=f"Geo {geo_code.upper()} -> Google",
            action_payload="https://google.com",
            schema="redirect",
            filters=[FlowFilter(name="country", mode="accept", payload=[geo_code])],
        )

        return await self.gateway.create_flow(geo_flow_data)

    async def create_offer_flow(self, campaign_id: int, offer_ids: list[int]) -> dict:

        share: float = int(100 / len(offer_ids))
        offers = []

        for id_ in offer_ids:
            offers.append(
                FlowOffer(
                    offer_id=id_,
                    share=share,
                )
            )

        offer_flow_data = FlowCreate(
            campaign_id=campaign_id,
            name="Offers",
            schema="landings",
            offers=offers,
        )

        return await self.gateway.create_flow(offer_flow_data)
