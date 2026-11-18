from typing import Annotated, Any

from app.constants import CAMPAIGN_NAME_PREFIX
from fastapi import APIRouter, Path, status

from app.api.dependencies import CampaignServiceDep, FlowServiceDep, KeitaroDep
from app.schemas.campaign import KeitaroCampaignCreateRequest, CampaignDeleteResponse

router = APIRouter(prefix="/campaigns", tags=["Campaigns"])


@router.get("")
async def get_campaigns(service: CampaignServiceDep):
    return await service.get_campaigns()


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_campaign(data: KeitaroCampaignCreateRequest, service: CampaignServiceDep):
    return await service.create_campaign(data)


@router.post("flow", status_code=status.HTTP_201_CREATED)
async def create_flow(service: FlowServiceDep):
    return await service.create_geo_flow(campaign_id=214150, geo_code="KZ")


# @router.get("/{campaign_id}")
# async def get_campaign(campaign_id: Annotated[int, Path(gt=0)], keitaro: KeitaroDep):
#     return await keitaro.get(f"/campaigns/{campaign_id}")


# @router.delete("/{campaign_id}", response_model=CampaignDeleteResponse)
# async def delete_campaign(campaign_id: Annotated[int, Path(gt=0)], keitaro: KeitaroDep):
#     await keitaro.delete(f"/campaigns/{campaign_id}")
#     return CampaignDeleteResponse(id=campaign_id, deleted=True)


# @router.get("/{campaign_id}/streams")
# async def get_campaign_streams(campaign_id: Annotated[int, Path(gt=0)], keitaro: KeitaroDep):
#     return await keitaro.get(f"/campaigns/{campaign_id}/streams")


# @router.post("/{campaign_id}/streams", status_code=status.HTTP_201_CREATED)
# async def create_campaign_stream(
#     campaign_id: Annotated[int, Path(gt=0)], payload: dict[str, Any], keitaro: KeitaroDep
# ):
#     # StreamRequest requires campaign_id, type, name, action_type and schema.
#     if payload.get("campaign_id") not in (None, campaign_id):
#         from fastapi import HTTPException

#         raise HTTPException(422, "campaign_id in body must match path parameter")
#     payload["campaign_id"] = campaign_id
#     return await keitaro.post("/streams", payload)


# @router.put("/streams/{stream_id}")
# async def update_stream(
#     stream_id: Annotated[int, Path(gt=0)], payload: dict[str, Any], keitaro: KeitaroDep
# ):
#     return await keitaro.put(f"/streams/{stream_id}", payload)


# @router.delete("/streams/{stream_id}")
# async def delete_stream(stream_id: Annotated[int, Path(gt=0)], keitaro: KeitaroDep):
#     return await keitaro.delete(f"/streams/{stream_id}")
