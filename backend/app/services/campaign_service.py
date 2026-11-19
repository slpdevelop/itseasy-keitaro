import logging
import json
import os
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING, Any, Awaitable, Callable

from app.core.config import Settings
from app.core.exceptions import CampaignCreationError, InvalidRequestError
from app.schemas.campaign import (
    CampaignCreatePayload,
    KTCampaignCreateResponse,
    KTCampaignCreateRequest,
)

if TYPE_CHECKING:
    from app.services.flow_service import FlowService
    from app.interfaces.campaign_gateway import CampaignGateway

logger = logging.getLogger(__name__)


class Checkpoint:
    """Запоминает результаты выполненных шагов. Есть запись, значит шаг уже сделан."""

    # Фиксированное имя в системной temp-папке (не mkdtemp: путь должен совпадать между запросами).
    DEFAULT_PATH = Path(tempfile.gettempdir()) / "campaign_checkpoint.json"

    def __init__(self, key: str, path=None):
        self.path = Path(path) if path else self.DEFAULT_PATH
        self.key = key  # например, имя кампании

    def _read(self) -> dict:
        return json.loads(self.path.read_text("utf-8")) if self.path.exists() else {}

    def _write(self, data: dict) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(".tmp")  # атомарная запись, чтобы не получить битый файл
        tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), "utf-8")
        os.replace(tmp, self.path)

    async def run(self, step: str, fn: Callable[[], Awaitable[Any]]) -> Any:
        done = self._read().get(self.key, {})
        if step in done:
            return done[step]  # шаг уже выполнен, берём сохранённый результат

        try:
            result = await fn()  # результат должен быть JSON-сериализуемым
        except Exception:
            logger.warning("Step %r failed for %r; next request resumes from it", step, self.key)
            raise

        # Перечитываем: пока шёл await, другой запрос мог записать свои данные.
        # Между чтением и записью нет await, поэтому в рамках event loop это атомарно.
        data = self._read()
        data.setdefault(self.key, {})[step] = result
        self._write(data)
        return result

    def clear(self) -> None:
        """Ручной сброс: начать операцию с нуля."""
        data = self._read()
        if data.pop(self.key, None) is not None:
            self._write(data)


class CampaignService:
    def __init__(
        self, gateway: "CampaignGateway", flow_service: "FlowService", settings: Settings
    ) -> None:
        self.gateway = gateway
        self.flow_service = flow_service
        self.settings = settings

    async def get_campaigns(self) -> list[dict]:
        campaigns = await self.gateway.get_campaigns()
        return [
            campaign
            for campaign in campaigns
            if (campaign.get("name") or "").startswith(self.settings.campaign_name_prefix)
        ]

    async def create_campaign(self, data: KTCampaignCreateRequest) -> KTCampaignCreateResponse:
        campaign_name = self._build_campaign_name(data.name)
        cp: Checkpoint = Checkpoint(key=campaign_name)

        campaign_id = await cp.run(
            "create_campaign",
            lambda: self._create_campaign_in_keitaro(campaign_name),
        )
        await cp.run(
            "create_geo_flow",
            lambda: self._create_geo_flow(campaign_id, data.country_code),
        )
        await cp.run(
            "create_offer_flow",
            lambda: self._create_offer_flow(campaign_id, data.offer_id_list),
        )
        await cp.run(
            "save_to_db",
            lambda: self._save_campaign_to_db(
                campaign_id, campaign_name, data.country_code, data.offer_id_list
            ),
        )

        return KTCampaignCreateResponse(
            campaign_id=campaign_id,
            campaign_name=campaign_name,
            message="Campaign and flows successfully created",
        )

    def _build_campaign_name(self, raw_name: str) -> str:
        name = raw_name
        if not name.startswith(self.settings.campaign_name_prefix):
            name = f"{self.settings.campaign_name_prefix}{name}"
        if len(name) > 255:
            raise InvalidRequestError("Campaign name exceeds the 255-character Keitaro limit")
        return name

    async def _create_campaign_in_keitaro(self, campaign_name: str) -> int:
        payload = CampaignCreatePayload(
            name=campaign_name,
            domain_id=self.settings.campaign_domain_id,
            group_id=self.settings.campaign_group_id,
            traffic_source_id=self.settings.campaign_traffic_source_id,
            state="active",
        )
        response = await self.gateway.create_campaign(payload)
        campaign_id = response.get("id") if isinstance(response, dict) else None
        if not isinstance(campaign_id, int) or campaign_id <= 0:
            raise CampaignCreationError("Keitaro did not return a valid campaign id")
        return campaign_id

    async def _create_geo_flow(self, campaign_id: int, country_code: str) -> None:
        await self.flow_service.create_geo_flow(campaign_id, country_code)

    async def _create_offer_flow(self, campaign_id: int, offer_id_list: list[int]) -> None:
        await self.flow_service.create_offer_flow(campaign_id, offer_id_list)

    async def _save_campaign_to_db(
        self,
        campaign_id: int,
        campaign_name: str,
        country_code: str,
        offer_id_list: list[int],
    ) -> None:
        """MOCK: заменить на реальную запись в БД (лучше upsert по campaign_id)."""
        logger.info(
            "[MOCK DB] saved campaign id=%s name=%s country=%s offers=%s",
            campaign_id,
            campaign_name,
            country_code,
            offer_id_list,
        )
