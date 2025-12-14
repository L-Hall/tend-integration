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
            # Fetch all data in parallel
            info, chores_raw, users_raw, leaderboard_raw = await asyncio.gather(
                self.api.async_get_info(),
                self.api.async_get_chores(),
                self.api.async_get_users(),
                self.api.async_get_leaderboard(),
            )
            
            chores = [_normalize_chore(chore) for chore in chores_raw]
            users = [_normalize_user(user) for user in users_raw]
            # If leaderboard is missing, derive a basic one from users
            leaderboard = leaderboard_raw or {"users": {u["id"]: u for u in users}}
            
            return {
                "info": info,
                "chores": chores,
                "users": users,
                "leaderboard": leaderboard,
                "version": info.get("version", "unknown"),
            }
        except ConnectionError as err:
            raise UpdateFailed(f"Error communicating with API: {err}") from err
    # Note: executor-based fetch was replaced with direct asyncio.gather above.


def _normalize_chore(chore: dict[str, Any]) -> dict[str, Any]:
    """Map upstream chore payload to the entity schema."""
    return {
        "id": chore.get("id") or chore.get("chore_id"),
        "title": chore.get("title") or chore.get("name") or "Unknown",
        "description": chore.get("description"),
        "points": chore.get("points"),
        "assigned_to": chore.get("assigned_to"),
        # Store status in frequency slot for lack of a better upstream field
        "frequency": chore.get("frequency") or chore.get("status"),
        "difficulty": chore.get("difficulty"),
        "room": chore.get("room"),
        "next_due": chore.get("next_due") or chore.get("due_at"),
        "last_completed_at": chore.get("last_completed_at") or chore.get("completed_at"),
        "is_overdue": chore.get("is_overdue", False),
    }


def _normalize_user(user: dict[str, Any]) -> dict[str, Any]:
    """Map upstream user payload to the entity schema."""
    return {
        "id": user.get("id") or user.get("user_id"),
        "name": user.get("name") or user.get("display_name") or "Unknown",
        "points": user.get("points", 0),
        "streak": user.get("streak") or user.get("streak_days", 0),
        "completed_today": user.get("completed_today", 0),
        "completed_week": user.get("completed_week", 0),
        "rank": user.get("rank"),
    }
