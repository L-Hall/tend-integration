"""Binary sensor platform for ChoreTracker."""
from __future__ import annotations

from typing import Any

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import ChoreTrackerCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up ChoreTracker binary sensors."""
    coordinator: ChoreTrackerCoordinator = hass.data[DOMAIN][config_entry.entry_id]
    
    entities: list[ChoreTrackerBinarySensor] = []
    
    # Wait for first data
    if not coordinator.data:
        await coordinator.async_request_refresh()
    
    # Create binary sensors for each chore (overdue status)
    chores = coordinator.data.get("chores", [])
    for chore in chores:
        entities.append(
            ChoreTrackerBinarySensor(
                coordinator=coordinator,
                config_entry=config_entry,
                chore_data=chore,
            )
        )
    
    async_add_entities(entities)


class ChoreTrackerBinarySensor(CoordinatorEntity[ChoreTrackerCoordinator], BinarySensorEntity):
    """ChoreTracker binary sensor for chore overdue status."""
    
    _attr_device_class = BinarySensorDeviceClass.PROBLEM
    
    def __init__(
        self,
        coordinator: ChoreTrackerCoordinator,
        config_entry: ConfigEntry,
        chore_data: dict[str, Any],
    ) -> None:
        """Initialize the binary sensor."""
        super().__init__(coordinator)
        self._chore_id = chore_data.get("id")
        self._chore_name = chore_data.get("title", "Unknown")
        self._attr_unique_id = f"{config_entry.entry_id}_chore_{self._chore_id}_overdue"
        self._attr_name = f"{self._chore_name} Overdue"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, config_entry.data["host"])},
            name="ChoreTracker",
            manufacturer="ChoreTracker",
            model="Hub",
        )
    
    @property
    def is_on(self) -> bool:
        """Return True if chore is overdue."""
        for chore in self.coordinator.data.get("chores", []):
            if chore.get("id") == self._chore_id:
                return chore.get("is_overdue", False)
        return False
    
    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra attributes."""
        for chore in self.coordinator.data.get("chores", []):
            if chore.get("id") == self._chore_id:
                return {
                    "assigned_to": chore.get("assigned_to"),
                    "last_completed": chore.get("last_completed_at"),
                    "next_due": chore.get("next_due"),
                    "frequency": chore.get("frequency"),
                }
        return {}