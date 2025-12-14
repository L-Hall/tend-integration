"""Tend integration for Home Assistant."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import DOMAIN
from .coordinator import FlowHomeCoordinator
from .api import FlowHomeAPI

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [
    Platform.SENSOR,
    Platform.BINARY_SENSOR,
    Platform.BUTTON,
]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Tend from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    
    session = async_get_clientsession(hass)
    api = FlowHomeAPI(
        session=session,
        host=entry.data["host"],
        port=entry.data.get("port", 8080),
        api_key=entry.data.get("api_key"),
    )
    
    coordinator = FlowHomeCoordinator(hass, api)
    await coordinator.async_config_entry_first_refresh()
    
    hass.data[DOMAIN][entry.entry_id] = coordinator
    
    # Register device
    device_registry = dr.async_get(hass)
    device_registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(DOMAIN, entry.data["host"])},
        manufacturer="Unburden LLP",
        model="Tend App",
        name=entry.title,
        sw_version=coordinator.data.get("version", "unknown"),
    )
    
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    
    # Register services
    async def handle_complete_chore(call: ServiceCall) -> None:
        """Handle the complete_chore service call."""
        chore_id = call.data.get("chore_id")
        user_id = call.data.get("user_id")
        
        await api.complete_chore(chore_id, user_id)
        await coordinator.async_request_refresh()
    
    async def handle_skip_chore(call: ServiceCall) -> None:
        """Handle the skip_chore service call."""
        chore_id = call.data.get("chore_id")
        user_id = call.data.get("user_id")
        reason = call.data.get("reason", "No reason provided")
        
        await api.skip_chore(chore_id, user_id, reason)
        await coordinator.async_request_refresh()
    
    hass.services.async_register(
        DOMAIN,
        "complete_chore",
        handle_complete_chore,
        schema={
            "chore_id": str,
            "user_id": str,
        },
    )
    
    hass.services.async_register(
        DOMAIN,
        "skip_chore",
        handle_skip_chore,
        schema={
            "chore_id": str,
            "user_id": str,
            "reason": str,
        },
    )
    
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)
    
    return unload_ok
