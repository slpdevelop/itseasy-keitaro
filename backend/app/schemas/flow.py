from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class FlowFilter(BaseModel):
    name: str
    mode: str
    payload: list[str]


class FlowOffer(BaseModel):
    offer_id: int
    share: int
    state: str = "active"


class FlowCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    campaign_id: int
    name: str
    type: str = "regular"
    schema_: str = Field(alias="schema")
    action_type: str = "http"
    action_payload: str = ""
    collect_clicks: bool = True

    filters: Optional[list[FlowFilter]] = None
    offers: Optional[list[FlowOffer]] = None
