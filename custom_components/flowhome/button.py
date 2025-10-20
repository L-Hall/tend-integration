"""Button platform for FlowHome."""
from __future__ import annotations

from typing import Any

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import FlowHomeCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up FlowHome buttons."""
    data = hass.data[DOMAIN][config_entry.entry_id]
    coordinator: FlowHomeCoordinator = data["coordinator"]
    
    entities: list[FlowHomeButton] = []
    
    # Wait for first data
    if not coordinator.data:
        await coordinator.async_request_refresh()
    
    # Create complete button for each chore
    chores = coordinator.data.get("chores", [])
    for chore in chores:
        entities.append(
            FlowHomeButton(
                coordinator=coordinator,
                config_entry=config_entry,
                chore_data=chore,
            )
        )
    
    async_add_entities(entities)


class FlowHomeButton(CoordinatorEntity[FlowHomeCoordinator], ButtonEntity):
    """FlowHome button to complete a chore."""
    
    def __init__(
        self,
        coordinator: FlowHomeCoordinator,
        config_entry: ConfigEntry,
        chore_data: dict[str, Any],
    ) -> None:
        """Initialize the button."""
        super().__init__(coordinator)
        self._chore_id = chore_data.get("id")
        self._chore_name = chore_data.get("title", "Unknown")
        self._attr_unique_id = f"{config_entry.entry_id}_chore_{self._chore_id}_complete"
        self._attr_name = f"Complete {self._chore_name}"
        self._attr_icon = "mdi:check-circle"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, config_entry.data["host"])},
            name="FlowHome",
            manufacturer="FlowHome",
            model="Hub",
        )
    
    async def async_press(self) -> None:
        """Handle the button press."""
        # Get the first user as default (in real implementation, this should be configurable)
        users = self.coordinator.data.get("users", [])
        if users:
            user_id = users[0].get("id")
            await self.coordinator.api.complete_chore(self._chore_id, user_id)
            await self.coordinator.async_request_refresh()
