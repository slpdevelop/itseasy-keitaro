from typing import Any
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.integrations.keitaro_api import KeitaroAPI
from app.core.exceptions import FlowNotFoundError, InvalidRequestError
from app.repositories.campaign_repository import CampaignRepository


class FlowService:
    """Business logic for flow/stream creation and synchronization.

    Orchestrates operations on campaign flows (streams) including:
    - Creation of GEO flows for geographic targeting
    - Creation of OFFER flows with traffic distribution
    - Pull sync from Keitaro (offer bindings into local DB)
    - Push sync to Keitaro (local changes to upstream)

    Uses dependency injection with KeitaroFlowGateway for API calls and
    CampaignRepository for local persistence operations.

    Attributes:
        gateway: KeitaroFlowGateway for HTTP requests to streams/flows API.
        repository: CampaignRepository for flow entity persistence.
    """

    def __init__(
        self,
        gateway: KeitaroFlowGateway,
        db_session: async_sessionmaker[AsyncSession],
    ) -> None:
        self.gateway: KeitaroFlowGateway = gateway
        self.db_session = db_session
