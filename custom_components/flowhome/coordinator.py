"""DataUpdateCoordinator for FlowHome."""
from __future__ import annotations

import asyncio
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
            info, chores, users, leaderboard = await asyncio.gather(
                self.api.async_get_info(),
                self.api.async_get_chores(),
                self.api.async_get_users(),
                self.api.async_get_leaderboard(),
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


