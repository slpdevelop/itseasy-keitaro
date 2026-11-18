"""HTTP client for the Keitaro Admin API v1."""

from __future__ import annotations

from typing import Any

import httpx
from fastapi import HTTPException


class KeitaroGateway:
    def __init__(self, base_url: str, api_key: str, timeout: int = 30) -> None:
        self.base_url = f"{base_url.rstrip('/')}/admin_api/v1"
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            headers={"Api-Key": api_key, "Accept": "application/json"},
            timeout=httpx.Timeout(timeout),
        )

    async def close(self) -> None:
        await self.client.aclose()

    async def request(self, method: str, path: str, **kwargs: Any) -> Any:
        try:
            response = await self.client.request(method, path, **kwargs)
        except httpx.TimeoutException as exc:
            raise HTTPException(504, "Keitaro API request timed out") from exc
        except httpx.RequestError as exc:
            raise HTTPException(502, "Could not connect to Keitaro API") from exc

        if response.status_code in (401, 403):
            raise HTTPException(response.status_code, "Keitaro authorization failed")
        if response.is_error:
            try:
                detail = response.json()
            except ValueError:
                detail = response.text[:1000]
            raise HTTPException(response.status_code, {"keitaro_error": detail})

        if response.status_code == 204 or not response.content:
            return None
        try:
            return response.json()
        except ValueError:
            return response.text

    async def get(self, path: str, **kwargs: Any) -> Any:
        return await self.request("GET", path, **kwargs)

    async def post(self, path: str, payload: dict[str, Any]) -> Any:
        return await self.request("POST", path, json=payload)

    async def put(self, path: str, payload: dict[str, Any]) -> Any:
        return await self.request("PUT", path, json=payload)

    async def delete(self, path: str) -> Any:
        return await self.request("DELETE", path)
