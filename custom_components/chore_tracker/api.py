"""API client for ChoreTracker app."""
from __future__ import annotations

import asyncio
import logging
from typing import Any

import aiohttp
import async_timeout

from .const import DEFAULT_PORT

_LOGGER = logging.getLogger(__name__)


class ChoreTrackerAPI:
    """ChoreTracker API client."""
    
    def __init__(
        self,
        session: aiohttp.ClientSession,
        host: str,
        port: int = DEFAULT_PORT,
        api_key: str | None = None,
    ) -> None:
        """Initialize API client."""
        self._session = session
        self._host = host
        self._port = port
        self._api_key = api_key
        self._base_url = f"http://{host}:{port}/api"
    
    async def async_get_info(self) -> dict[str, Any]:
        """Get ChoreTracker app info."""
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
                    method,
                    url,
                    json=json,
                    headers=headers,
                ) as response:
                    response.raise_for_status()
                    return await response.json()
        except asyncio.TimeoutError as err:
            raise ConnectionError("Timeout connecting to ChoreTracker") from err
        except aiohttp.ClientError as err:
            raise ConnectionError(f"Error connecting to ChoreTracker: {err}") from err