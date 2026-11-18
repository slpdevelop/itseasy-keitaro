from typing import Annotated

from fastapi import APIRouter, Path

from app.api.dependencies import KeitaroDep

router = APIRouter(prefix="/offers", tags=["Offers"])


@router.get("")
async def get_offers(keitaro: KeitaroDep):
    return await keitaro.get("/offers")


@router.get("/{offer_id}")
async def get_offer(offer_id: Annotated[int, Path(gt=0)], keitaro: KeitaroDep):
    return await keitaro.get(f"/offers/{offer_id}")
