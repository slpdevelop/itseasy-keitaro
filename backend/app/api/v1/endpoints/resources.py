from fastapi import APIRouter
from app.api.dependencies import KeitaroDep

router = APIRouter(tags=["Keitaro resources"])


@router.get("/domains")
async def get_domains(keitaro: KeitaroDep):
    return await keitaro.get("/domains")


@router.get("/groups")
async def get_groups(keitaro: KeitaroDep):
    return await keitaro.get("/groups")


@router.get("/traffic-sources")
async def get_traffic_sources(keitaro: KeitaroDep):
    return await keitaro.get("/traffic_sources")


@router.get("/stream-filters")
async def get_stream_filters(keitaro: KeitaroDep):
    return await keitaro.get("/stream_filters")


@router.get("/stream-schemas")
async def get_stream_schemas(keitaro: KeitaroDep):
    return await keitaro.get("/stream_schemas")


@router.get("/stream-types")
async def get_stream_types(keitaro: KeitaroDep):
    return await keitaro.get("/stream_types")


@router.get("/streams-actions")
async def get_stream_actions(keitaro: KeitaroDep):
    return await keitaro.get("/streams_actions")
