"""FlowHome integration for Home Assistant."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers import config_validation as cv
import voluptuous as vol

from .const import (
    DOMAIN,
    SERVICE_COMPLETE_CHORE,
    SERVICE_SKIP_CHORE,
    SERVICE_REGISTER_WEBHOOK,
    SERVICE_UNREGISTER_WEBHOOK,
)
from .coordinator import FlowHomeCoordinator
from .api import FlowHomeAPI
from .webhook_manager import FlowHomeWebhookManager

COMPLETE_CHORE_SCHEMA = vol.Schema(
    {
        vol.Required("chore_id"): cv.string,
        vol.Required("user_id"): cv.string,
    }
)

SKIP_CHORE_SCHEMA = vol.Schema(
    {
        vol.Required("chore_id"): cv.string,
        vol.Required("user_id"): cv.string,
        vol.Optional("reason", default="No reason provided"): cv.string,
    }
)

REGISTER_WEBHOOK_SCHEMA = vol.Schema(
    {
        vol.Optional("webhook_id"): cv.string,
        vol.Optional("name", default="FlowHome webhook"): cv.string,
        vol.Optional("local_only", default=True): cv.boolean,
    }
)

UNREGISTER_WEBHOOK_SCHEMA = vol.Schema(
    {vol.Required("webhook_id"): cv.string}
)

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [
    Platform.SENSOR,
    Platform.BINARY_SENSOR,
    Platform.BUTTON,
]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up FlowHome from a config entry."""
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

    webhook_manager = FlowHomeWebhookManager(hass, entry)
    await webhook_manager.async_initialize()

    hass.data[DOMAIN][entry.entry_id] = {
        "coordinator": coordinator,
        "webhooks": webhook_manager,
    }
    
    # Register device
    device_registry = dr.async_get(hass)
    device_registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(DOMAIN, entry.data["host"])},
        manufacturer="FlowHome",
        model="FlowHome App",
        name=entry.title,
        sw_version=coordinator.data.get("version", "unknown"),
    )
    
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    
    # Register services
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator = data["coordinator"]
    webhook_manager = data["webhooks"]

    async def handle_complete_chore(call: ServiceCall) -> None:
        """Handle the complete_chore service call."""
        chore_id = call.data["chore_id"]
        user_id = call.data["user_id"]

        await api.complete_chore(chore_id, user_id)
        await coordinator.async_request_refresh()
    
    async def handle_skip_chore(call: ServiceCall) -> None:
        """Handle the skip_chore service call."""
        chore_id = call.data["chore_id"]
        user_id = call.data["user_id"]
        reason = call.data["reason"]

        await api.skip_chore(chore_id, user_id, reason)
        await coordinator.async_request_refresh()

    async def handle_register_webhook(call: ServiceCall) -> dict[str, str]:
        """Register a webhook for FlowHome."""
        result = await webhook_manager.async_register(
            name=call.data.get("name", "FlowHome webhook"),
            local_only=call.data.get("local_only", True),
            webhook_id=call.data.get("webhook_id"),
        )
        return result

    async def handle_unregister_webhook(call: ServiceCall) -> dict[str, str]:
        """Unregister a FlowHome webhook."""
        webhook_id = call.data.get("webhook_id")
        if not webhook_id:
            raise HomeAssistantError("Missing webhook_id")
        await webhook_manager.async_unregister(webhook_id)
        return {"webhook_id": webhook_id}

    hass.services.async_register(
        DOMAIN,
        SERVICE_COMPLETE_CHORE,
        handle_complete_chore,
        schema=COMPLETE_CHORE_SCHEMA,
    )
    
    hass.services.async_register(
        DOMAIN,
        SERVICE_SKIP_CHORE,
        handle_skip_chore,
        schema=SKIP_CHORE_SCHEMA,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_REGISTER_WEBHOOK,
        handle_register_webhook,
        schema=REGISTER_WEBHOOK_SCHEMA,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_UNREGISTER_WEBHOOK,
        handle_unregister_webhook,
        schema=UNREGISTER_WEBHOOK_SCHEMA,
    )
    
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    data = hass.data[DOMAIN].get(entry.entry_id)
    webhook_manager: FlowHomeWebhookManager | None = None
    if data:
        webhook_manager = data.get("webhooks")

    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        if webhook_manager is not None:
            await webhook_manager.async_unload()
        hass.data[DOMAIN].pop(entry.entry_id, None)

    return unload_ok
