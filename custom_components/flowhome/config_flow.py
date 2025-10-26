"""Config flow for FlowHome integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.components import zeroconf
from homeassistant.const import CONF_HOST, CONF_NAME, CONF_PORT
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import DOMAIN, DEFAULT_HOST, DEFAULT_PORT, CONF_USE_SSL
from .api import FlowHomeAPI

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Optional(CONF_HOST, default=DEFAULT_HOST): str,
        vol.Optional(CONF_PORT, default=DEFAULT_PORT): int,
        vol.Optional("api_key"): str,
    }
)


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validate the user input allows us to connect."""
    session = async_get_clientsession(hass)
    host_input = data.get(CONF_HOST, DEFAULT_HOST)
    host, port, use_ssl = FlowHomeAPI.normalize_connection(
        host_input,
        data.get(CONF_PORT),
    )
    api = FlowHomeAPI(
        session=session,
        host=host,
        port=port,
        use_ssl=use_ssl,
        api_key=data.get("api_key"),
    )
    
    # Test the connection
    try:
        info = await api.async_get_info()
    except ConnectionError as err:
        raise CannotConnect from err
    
    return {
        "title": info.get("household_name", "FlowHome"),
        "host": host,
        "port": port,
        "use_ssl": use_ssl,
        "unique_id": host,
    }


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for FlowHome."""
    
    VERSION = 1
    
    def __init__(self) -> None:
        """Initialize."""
        self._discovered_host: str | None = None
        self._discovered_name: str | None = None
        self._discovered_port: int | None = None
        self._discovered_use_ssl: bool = False
    
    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}
        
        if user_input is not None:
            try:
                info = await validate_input(self.hass, user_input)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                # Check if already configured
                await self.async_set_unique_id(info["unique_id"])
                self._abort_if_unique_id_configured()
                
                entry_data = {
                    CONF_HOST: info["host"],
                    CONF_PORT: info["port"],
                }
                if user_input.get("api_key"):
                    entry_data["api_key"] = user_input["api_key"]
                if info["use_ssl"]:
                    entry_data[CONF_USE_SSL] = True
                
                return self.async_create_entry(
                    title=info["title"],
                    data=entry_data,
                )
        
        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )
    
    async def async_step_zeroconf(
        self, discovery_info: zeroconf.ZeroconfServiceInfo
    ) -> FlowResult:
        """Handle zeroconf discovery."""
        host = discovery_info.host
        name = discovery_info.name.replace("._flowhome._tcp.local.", "")
        
        # Check if already configured
        normalized_host, normalized_port, use_ssl = FlowHomeAPI.normalize_connection(
            host,
            discovery_info.port or DEFAULT_PORT,
        )
        await self.async_set_unique_id(normalized_host)
        self._abort_if_unique_id_configured(updates={CONF_HOST: normalized_host})
        
        self._discovered_host = normalized_host
        self._discovered_name = name
        self._discovered_port = normalized_port
        self._discovered_use_ssl = use_ssl
        
        # Check if we can connect
        try:
            session = async_get_clientsession(self.hass)
            api = FlowHomeAPI(
                session=session,
                host=normalized_host,
                port=normalized_port,
                use_ssl=use_ssl,
            )
            await api.async_get_info()
        except Exception:  # pylint: disable=broad-except
            return self.async_abort(reason="cannot_connect")
        
        return await self.async_step_zeroconf_confirm()
    
    async def async_step_zeroconf_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle user-confirmation of discovered FlowHome."""
        if user_input is not None:
            entry_data = {
                CONF_HOST: self._discovered_host,
                CONF_PORT: self._discovered_port or DEFAULT_PORT,
            }
            if self._discovered_use_ssl:
                entry_data[CONF_USE_SSL] = True
            return self.async_create_entry(
                title=self._discovered_name or "FlowHome",
                data=entry_data,
            )
        
        return self.async_show_form(
            step_id="zeroconf_confirm",
            description_placeholders={
                CONF_NAME: self._discovered_name,
                CONF_HOST: self._discovered_host,
            },
        )


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidAuth(HomeAssistantError):
    """Error to indicate there is invalid auth."""

