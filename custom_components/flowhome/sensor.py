"""Sensor platform for FlowHome."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, ATTR_POINTS, ATTR_STREAK, ATTR_USER_NAME
from .coordinator import FlowHomeCoordinator


@dataclass
class FlowHomeSensorEntityDescription(SensorEntityDescription):
    """Describes FlowHome sensor entity."""
    
    value_fn: Callable[[dict[str, Any]], Any] = lambda data: None
    attributes_fn: Callable[[dict[str, Any]], dict[str, Any]] = lambda data: {}


def get_user_points(user_id: str) -> Callable:
    """Get points for a specific user."""
    def _get_points(data: dict[str, Any]) -> int:
        leaderboard = data.get("leaderboard", {})
        user_data = leaderboard.get("users", {}).get(user_id, {})
        return user_data.get("points", 0)
    return _get_points


def get_user_attributes(user_id: str) -> Callable:
    """Get attributes for a specific user."""
    def _get_attributes(data: dict[str, Any]) -> dict[str, Any]:
        leaderboard = data.get("leaderboard", {})
        user_data = leaderboard.get("users", {}).get(user_id, {})
        return {
            ATTR_STREAK: user_data.get("streak", 0),
            "completed_today": user_data.get("completed_today", 0),
            "completed_week": user_data.get("completed_week", 0),
            "rank": user_data.get("rank", 0),
        }
    return _get_attributes


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up FlowHome sensors."""
    coordinator: FlowHomeCoordinator = hass.data[DOMAIN][config_entry.entry_id]
    
    entities: list[FlowHomeSensor] = []
    
    # Wait for first data
    if not coordinator.data:
        await coordinator.async_request_refresh()
    
    # Create sensors for each user
    users = coordinator.data.get("users", [])
    for user in users:
        user_id = user.get("id")
        user_name = user.get("name", "Unknown")
        
        # Points sensor for each user
        entities.append(
            FlowHomeSensor(
                coordinator=coordinator,
                config_entry=config_entry,
                description=FlowHomeSensorEntityDescription(
                    key=f"user_{user_id}_points",
                    name=f"{user_name} Points",
                    native_unit_of_measurement="points",
                    state_class=SensorStateClass.TOTAL,
                    icon="mdi:star",
                    value_fn=get_user_points(user_id),
                    attributes_fn=get_user_attributes(user_id),
                ),
                user_id=user_id,
                user_name=user_name,
            )
        )
    
    # Create sensors for each chore
    chores = coordinator.data.get("chores", [])
    for chore in chores:
        chore_id = chore.get("id")
        chore_name = chore.get("title", "Unknown")
        
        # Last completed sensor for each chore
        entities.append(
            FlowHomeChoreSensor(
                coordinator=coordinator,
                config_entry=config_entry,
                chore_data=chore,
            )
        )
    
    # Total household points sensor
    entities.append(
        FlowHomeSensor(
            coordinator=coordinator,
            config_entry=config_entry,
            description=FlowHomeSensorEntityDescription(
                key="household_points",
                name="Household Total Points",
                native_unit_of_measurement="points",
                state_class=SensorStateClass.TOTAL,
                icon="mdi:home-heart",
                value_fn=lambda data: sum(
                    user.get("points", 0)
                    for user in data.get("leaderboard", {}).get("users", {}).values()
                ),
            ),
        )
    )
    
    async_add_entities(entities)


class FlowHomeSensor(CoordinatorEntity[FlowHomeCoordinator], SensorEntity):
    """FlowHome sensor entity."""
    
    entity_description: FlowHomeSensorEntityDescription
    
    def __init__(
        self,
        coordinator: FlowHomeCoordinator,
        config_entry: ConfigEntry,
        description: FlowHomeSensorEntityDescription,
        user_id: str | None = None,
        user_name: str | None = None,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{config_entry.entry_id}_{description.key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, config_entry.data["host"])},
            name="FlowHome",
            manufacturer="FlowHome",
            model="Hub",
        )
        self._user_id = user_id
        self._user_name = user_name
    
    @property
    def native_value(self) -> Any:
        """Return the state of the sensor."""
        return self.entity_description.value_fn(self.coordinator.data)
    
    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra attributes."""
        attrs = self.entity_description.attributes_fn(self.coordinator.data)
        if self._user_name:
            attrs[ATTR_USER_NAME] = self._user_name
        return attrs


class FlowHomeChoreSensor(CoordinatorEntity[FlowHomeCoordinator], SensorEntity):
    """FlowHome chore sensor entity."""
    
    def __init__(
        self,
        coordinator: FlowHomeCoordinator,
        config_entry: ConfigEntry,
        chore_data: dict[str, Any],
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._chore_id = chore_data.get("id")
        self._chore_name = chore_data.get("title", "Unknown")
        self._attr_unique_id = f"{config_entry.entry_id}_chore_{self._chore_id}"
        self._attr_name = f"Chore: {self._chore_name}"
        self._attr_icon = "mdi:broom"
        self._attr_device_class = SensorDeviceClass.TIMESTAMP
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, config_entry.data["host"])},
            name="FlowHome",
            manufacturer="FlowHome",
            model="Hub",
        )
    
    @property
    def native_value(self) -> datetime | None:
        """Return when the chore was last completed."""
        for chore in self.coordinator.data.get("chores", []):
            if chore.get("id") == self._chore_id:
                last_completed = chore.get("last_completed_at")
                if last_completed:
                    return datetime.fromisoformat(last_completed)
        return None
    
    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra attributes."""
        for chore in self.coordinator.data.get("chores", []):
            if chore.get("id") == self._chore_id:
                return {
                    "assigned_to": chore.get("assigned_to"),
                    "room": chore.get("room"),
                    "frequency": chore.get("frequency"),
                    "difficulty": chore.get("difficulty"),
                    "points": chore.get("points"),
                    "is_overdue": chore.get("is_overdue", False),
                    "next_due": chore.get("next_due"),
                }
        return {}