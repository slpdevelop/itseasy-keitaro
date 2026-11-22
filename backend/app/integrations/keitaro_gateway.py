"""HTTP client wrapper for the Keitaro Admin API v1."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

import httpx

from app.core.exceptions import KeitaroClientError, KeitaroError, KeitaroNotFoundError, KeitaroTimeoutError

logger = logging.getLogger(__name__)


class KeitaroGateway:
    """Central gateway for authenticated HTTP requests to the Keitaro Admin API.

    Provides a unified interface for interacting with Keitaro services. Handles:
    - Base URL construction from settings
    - Api-Key header injection for authentication
    - Timeout enforcement (configurable via settings)
    - Error translation (404 → KeitaroNotFoundError, other HTTP errors → KeitaroError,
      timeouts → KeitaroTimeoutError)
    - Empty response handling (204 No Content → None)

    The underlying httpx.AsyncClient is injected at startup and reused across
    requests to maintain connection pooling efficiency. Never create new clients
    outside of lifespan/startup code.

    Args:
        client: Singleton httpx.AsyncClient instance with base_url, headers, timeout.
    """

    def __init__(self, client: httpx.AsyncClient) -> None:
        """Initialize gateway with shared HTTP client.

        Args:
            client: Pre-configured httpx.AsyncClient with Keitaro credentials and settings.
        """
        self.client = client

    async def request(self, method: str, path: str, **kwargs: Any) -> Any:
        """Execute an upstream request; retry transient GET failures only."""
        attempts = 3 if method.upper() == "GET" else 1
        for attempt in range(attempts):
            try:
                response = await self.client.request(method, path, **kwargs)
            except httpx.TimeoutException as exc:
                if attempt + 1 < attempts:
                    await asyncio.sleep(0.2 * (2 ** attempt))
                    continue
                raise KeitaroTimeoutError() from exc
            except httpx.RequestError as exc:
                if attempt + 1 < attempts:
                    await asyncio.sleep(0.2 * (2 ** attempt))
                    continue
                raise KeitaroError() from exc

            if response.is_error:
                logger.warning(
                    "Keitaro %s %s returned HTTP %s", method, path, response.status_code
                )
                if response.status_code == 404:
                    raise KeitaroNotFoundError()
                if 400 <= response.status_code < 500:
                    raise KeitaroClientError(response.status_code)
                if attempt + 1 < attempts:
                    await asyncio.sleep(0.2 * (2 ** attempt))
                    continue
                raise KeitaroError()

            if response.status_code == 204 or not response.content:
                return None
            try:
                return response.json()
            except ValueError as exc:
                raise KeitaroError("Keitaro returned a non-JSON success response") from exc
        raise KeitaroError()

    async def get(self, path: str, **kwargs: Any) -> Any:
        """Execute GET request to Keitaro API.

        Convenience wrapper for fetches like campaigns, flows, offers lists.
        All GET requests include Api-Key header and respect timeout settings.

        Args:
            path: API endpoint path.
            **kwargs: Additional GET-specific arguments (params).

        Returns:
            Parsed JSON or None.

        Raises:
            KeitaroError / KeitaroTimeoutError per request method behavior.
        """
        return await self.request("GET", path, **kwargs)

    async def post(self, path: str, payload: dict[str, Any]) -> Any:
        """Execute POST request to Keitaro API with JSON payload.

        Used for creating entities (campaigns, flows, offers). Payload is
        serialized to JSON and sent in request body. Returns created entity data.

        Args:
            path: API endpoint path for creation (e.g., "/streams").
            payload: Dictionary of fields for the new entity.

        Returns:
            Created resource JSON or None.

        Raises:
            KeitaroError on HTTP failure or invalid response format.
        """
        return await self.request("POST", path, json=payload)

    async def put(self, path: str, payload: dict[str, Any]) -> Any:
        """Execute PUT request to update an existing resource.

        Used for partial updates (e.g., changing flow offers). Only specified
        fields are updated; others remain unchanged. Payload is sent as JSON.

        Args:
            path: API endpoint path for update (e.g., "/streams/123").
            payload: Dictionary of fields to update.

        Returns:
            Updated resource JSON or None.

        Raises:
            KeitaroError on HTTP failure or invalid response format.
        """
        return await self.request("PUT", path, json=payload)
