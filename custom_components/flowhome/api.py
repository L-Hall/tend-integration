"""API client for FlowHome app."""
from __future__ import annotations

import asyncio
import logging
from typing import Any

import aiohttp
import async_timeout
from urllib.parse import urlparse

from .const import DEFAULT_PORT

_LOGGER = logging.getLogger(__name__)


class FlowHomeAPI:
    """FlowHome API client."""
    
    def __init__(
        self,
        session: aiohttp.ClientSession,
        host: str,
        port: int = DEFAULT_PORT,
        api_key: str | None = None,
    ) -> None:
        """Initialize API client."""
        self._session = session
        # Allow full URLs (with scheme/port) or plain hostnames. Default to https when using port 443.
        parsed = urlparse(host if "://" in host else f"//{host}", scheme="http")
        self._host = parsed.hostname or host
        self._port = parsed.port or port
        self._scheme = parsed.scheme
        if self._port in (443, 8443) and self._scheme == "http":
            self._scheme = "https"
        self._api_key = api_key
        base = f"{self._scheme}://{self._host}"
        if self._port:
            base += f":{self._port}"
        self._base_url = f"{base}/api"
    
    async def async_get_info(self) -> dict[str, Any]:
        """Get FlowHome app info."""
        return await self._request("GET", "/info")
    
    async def async_get_chores(self) -> list[dict[str, Any]]:
        """Get all chores."""
        return await self._request("GET", "/chores")
    
    async def async_get_users(self) -> list[dict[str, Any]]:
        """Get all household members."""
        return await self._request("GET", "/users")
    
    async def async_get_leaderboard(self) -> dict[str, Any]:
        """Get leaderboard data."""
        return await self._request("GET", "/leaderboard")
    
    async def complete_chore(self, chore_id: str, user_id: str) -> None:
        """Mark a chore as complete."""
        await self._request(
            "POST",
            f"/chores/{chore_id}/complete",
            json={"user_id": user_id},
        )
    
    async def skip_chore(self, chore_id: str, user_id: str, reason: str) -> None:
        """Skip a chore."""
        await self._request(
            "POST",
            f"/chores/{chore_id}/skip",
            json={"user_id": user_id, "reason": reason},
        )
    
    async def _request(
        self,
        method: str,
        path: str,
        json: dict[str, Any] | None = None,
    ) -> Any:
        """Make a request to the API."""
        headers = {}
        if self._api_key:
            headers["Authorization"] = f"Bearer {self._api_key}"
        
        url = f"{self._base_url}{path}"
        
        try:
            async with async_timeout.timeout(10):
                async with self._session.request(
                    method=method,
                    url=url,
                    json=json,
                    headers=headers,
                ) as response:
                    response.raise_for_status()
                    return await response.json()
        except asyncio.TimeoutError as err:
            raise ConnectionError("Timeout connecting to FlowHome") from err
        except aiohttp.ClientError as err:
            raise ConnectionError(f"Error connecting to FlowHome: {err}") from err
