"""DataUpdateCoordinator for FlowHome."""
from __future__ import annotations

from datetime import timedelta
import logging
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import FlowHomeAPI
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


class FlowHomeCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """FlowHome data update coordinator."""
    
    def __init__(self, hass: HomeAssistant, api: FlowHomeAPI) -> None:
        """Initialize coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=30),
        )
        self.api = api
    
    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from API endpoint."""
        try:
            # Fetch all data in parallel
            info, chores, users, leaderboard = await self.hass.async_add_executor_job(
                self._fetch_all_data
            )
            
            return {
                "info": info,
                "chores": chores,
                "users": users,
                "leaderboard": leaderboard,
                "version": info.get("version", "unknown"),
            }
        except ConnectionError as err:
            raise UpdateFailed(f"Error communicating with API: {err}") from err
    
    async def _fetch_all_data(self) -> tuple:
        """Fetch all data from the API."""
        info = await self.api.async_get_info()
        chores = await self.api.async_get_chores()
        users = await self.api.async_get_users()
        leaderboard = await self.api.async_get_leaderboard()
        
        return info, chores, users, leaderboard