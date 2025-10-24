"""API client for FlowHome app."""
from __future__ import annotations

import asyncio
import logging
from typing import Any
from urllib.parse import urlparse

import aiohttp
import async_timeout

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
        use_ssl: bool | None = None,
    ) -> None:
        """Initialize API client."""
        self._session = session
        normalized_host, normalized_port, resolved_ssl = self.normalize_connection(
            host,
            port,
            use_ssl,
        )
        self._host = normalized_host
        self._port = normalized_port
        self._use_ssl = resolved_ssl
        self._api_key = api_key
        scheme = "https" if self._use_ssl else "http"
        port_suffix = f":{self._port}" if self._port else ""
        self._base_url = f"{scheme}://{self._host}{port_suffix}/api"
    
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
                    method,
                    url,
                    json=json,
                    headers=headers,
                ) as response:
                    response.raise_for_status()
                    return await response.json()
        except asyncio.TimeoutError as err:
            raise ConnectionError("Timeout connecting to FlowHome") from err
        except aiohttp.ClientError as err:
            raise ConnectionError(f"Error connecting to FlowHome: {err}") from err

    @staticmethod
    def normalize_connection(
        host: str,
        port: int | None = None,
        use_ssl: bool | None = None,
    ) -> tuple[str, int, bool]:
        """Normalize host, port, and SSL usage from user/discovery input."""
        if not host:
            raise ConnectionError("Host is required")

        raw_host = host.strip()
        raw_host = raw_host.rstrip("/")

        url_to_parse = raw_host if "://" in raw_host else f"http://{raw_host}"
        parsed = urlparse(url_to_parse)

        hostname = parsed.hostname or parsed.path
        if not hostname:
            raise ConnectionError("Invalid host provided")

        detected_port = parsed.port
        has_explicit_port = detected_port is not None
        scheme_ssl = parsed.scheme == "https"

        # Respect explicit host port even when a default was supplied downstream.
        if has_explicit_port and (port in (None, 0, DEFAULT_PORT)):
            resolved_port = detected_port
        else:
            resolved_port = port or detected_port or DEFAULT_PORT

        resolved_ssl = use_ssl if use_ssl is not None else scheme_ssl

        return hostname, resolved_port, resolved_ssl
