"""HTTP client wrapper for the Keitaro Admin API v1."""

from __future__ import annotations

import logging
from typing import Any

import httpx

from app.core.exceptions import KeitaroError, KeitaroTimeoutError

logger = logging.getLogger(__name__)


class KeitaroGateway:
    def __init__(self, client: httpx.AsyncClient) -> None:
        self.client = client

    async def request(self, method: str, path: str, **kwargs: Any) -> Any:
        try:
            response = await self.client.request(method, path, **kwargs)
        except httpx.TimeoutException as exc:
            raise KeitaroTimeoutError() from exc
        except httpx.RequestError as exc:
            raise KeitaroError() from exc

        if response.is_error:
            # 401/403 from Keitaro concern the server-side API key, not the API caller.
            logger.warning("Keitaro returned HTTP %s", response.status_code)
            raise KeitaroError()

        if response.status_code == 204 or not response.content:
            return None
        try:
            return response.json()
        except ValueError as exc:
            raise KeitaroError("Keitaro returned a non-JSON success response") from exc

    async def get(self, path: str, **kwargs: Any) -> Any:
        return await self.request("GET", path, **kwargs)

    async def post(self, path: str, payload: dict[str, Any]) -> Any:
        return await self.request("POST", path, json=payload)

    async def put(self, path: str, payload: dict[str, Any]) -> Any:
        return await self.request("PUT", path, json=payload)

    async def delete(self, path: str) -> Any:
        return await self.request("DELETE", path)
