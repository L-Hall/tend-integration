"""API client for FlowHome app."""
from __future__ import annotations

import asyncio
import logging
from typing import Any
from urllib.parse import urlparse

import aiohttp
import async_timeout

from .const import DEFAULT_HOST, DEFAULT_PORT

_LOGGER = logging.getLogger(__name__)


class FlowHomeAPI:
    """FlowHome API client."""
    
    def __init__(
        self,
        session: aiohttp.ClientSession,
        host: str,
        port: int | None = DEFAULT_PORT,
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
        include_port = (
            self._port is not None
            and not (
                (self._use_ssl and self._port == 443)
                or (not self._use_ssl and self._port == 80)
            )
        )
        port_suffix = f":{self._port}" if include_port else ""
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

        url_to_parse = raw_host if "://" in raw_host else f"https://{raw_host}"
        parsed = urlparse(url_to_parse)

        hostname = parsed.hostname or parsed.path
        if not hostname:
            raise ConnectionError("Invalid host provided")

        detected_port = parsed.port
        has_explicit_port = detected_port is not None
        scheme_ssl = parsed.scheme == "https"

        candidate_port = detected_port if has_explicit_port else port

        if use_ssl is not None:
            resolved_ssl = use_ssl
        else:
            resolved_ssl = scheme_ssl or (candidate_port == 443) or (
                hostname == DEFAULT_HOST and candidate_port in (None, 0)
            )

        fallback_port = 443 if resolved_ssl else 80

        if has_explicit_port:
            resolved_port = detected_port
        elif candidate_port not in (None, 0):
            resolved_port = candidate_port
        else:
            resolved_port = fallback_port

        return hostname, resolved_port, resolved_ssl
