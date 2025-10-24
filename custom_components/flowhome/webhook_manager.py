"""Webhook management for FlowHome integration."""
from __future__ import annotations

import json
import logging
from typing import Any

from aiohttp import web

from homeassistant.components import webhook
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.storage import Store

from .const import DOMAIN, EVENT_WEBHOOK_RECEIVED

_LOGGER = logging.getLogger(__name__)

STORE_VERSION = 1


class FlowHomeWebhookManager:
    """Manage FlowHome webhooks and persistence."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the webhook manager."""
        self._hass = hass
        self._entry = entry
        self._store = Store(hass, STORE_VERSION, f"{DOMAIN}_webhooks_{entry.entry_id}")
        self._webhooks: dict[str, dict[str, Any]] = {}

    async def async_initialize(self) -> None:
        """Load stored webhooks and register them with HA."""
        stored = await self._store.async_load() or {}
        for webhook_id, info in stored.items():
            await self._register_internal(
                webhook_id,
                info.get("name", "FlowHome webhook"),
                info.get("local_only", True),
            )

    async def async_unload(self) -> None:
        """Unregister all webhooks when config entry is unloaded."""
        for webhook_id in list(self._webhooks):
            _LOGGER.debug("Unregistering webhook %s for %s", webhook_id, self._entry.entry_id)
            webhook.async_unregister(self._hass, webhook_id)
        self._webhooks.clear()

    async def async_register(
        self,
        *,
        name: str,
        local_only: bool,
        webhook_id: str | None = None,
    ) -> dict[str, str]:
        """Register a webhook (creating one if necessary)."""
        if webhook_id and webhook_id in self._webhooks:
            # Already registered; return current URL
            return {
                "webhook_id": webhook_id,
                "webhook_url": webhook.async_generate_url(self._hass, webhook_id),
            }

        if webhook_id is None:
            generate = getattr(webhook, "async_generate_id", None)
            if callable(generate):
                webhook_id = generate()
            else:
                webhook_id = webhook.generate_secret()
        await self._register_internal(webhook_id, name, local_only)
        await self._async_save()

        return {
            "webhook_id": webhook_id,
            "webhook_url": webhook.async_generate_url(self._hass, webhook_id),
        }

    async def async_unregister(self, webhook_id: str) -> None:
        """Unregister a webhook and remove it from storage."""
        if webhook_id in self._webhooks:
            webhook.async_unregister(self._hass, webhook_id)
            self._webhooks.pop(webhook_id, None)
            await self._async_save()

    async def _register_internal(
        self,
        webhook_id: str,
        name: str,
        local_only: bool,
    ) -> None:
        """Register webhook handler with Home Assistant."""
        webhook.async_register(
            self._hass,
            DOMAIN,
            name,
            webhook_id,
            self._async_handle_webhook,
            local_only=local_only,
        )
        self._webhooks[webhook_id] = {
            "name": name,
            "local_only": local_only,
        }

    async def _async_handle_webhook(self, webhook_id: str, request: web.Request) -> web.Response:
        """Handle incoming webhook payload from FlowHome app."""
        try:
            payload = await request.json()
        except (json.decoder.JSONDecodeError, TypeError):
            payload = {}

        self._hass.bus.async_fire(
            EVENT_WEBHOOK_RECEIVED,
            {
                "entry_id": self._entry.entry_id,
                "webhook_id": webhook_id,
                "payload": payload,
                "query": dict(request.query),
                "source": request.remote,
            },
        )

        return web.Response(status=200)

    async def _async_save(self) -> None:
        """Persist webhook metadata to disk."""
        await self._store.async_save(self._webhooks)
