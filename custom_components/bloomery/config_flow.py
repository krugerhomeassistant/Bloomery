"""Config flow for Bloomery: paste the integration URL shown in Bloomery's profile."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_URL
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import BloomeryAuthError, BloomeryClient, BloomeryConnectionError, normalize_url
from .const import DOMAIN

SCHEMA = vol.Schema({vol.Required(CONF_URL): str})


class BloomeryConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Bloomery."""

    VERSION = 1

    async def _validate(self, user_input: dict[str, Any]) -> tuple[str | None, dict[str, Any], dict[str, str]]:
        """Return (normalized url, feed data, errors) and set the unique id (server host + Bloomery user id)."""
        url = normalize_url(user_input[CONF_URL])
        if not url:
            return None, {}, {CONF_URL: "invalid_url"}
        client = BloomeryClient(async_get_clientsession(self.hass), url, self.hass.config.time_zone)
        try:
            data = await client.async_get_state()
        except BloomeryAuthError:
            return None, {}, {CONF_URL: "invalid_token"}
        except BloomeryConnectionError:
            return None, {}, {"base": "cannot_connect"}
        host = url.split("://", 1)[1].split("/", 1)[0]
        await self.async_set_unique_id(f"{host}_{data['user_id']}")
        return url, data, {}

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input:
            url, data, errors = await self._validate(user_input)
            if url:
                self._abort_if_unique_id_configured(updates={CONF_URL: url})
                return self.async_create_entry(title=f"Bloomery ({data['name']})", data={CONF_URL: url})
        return self.async_show_form(step_id="user", data_schema=SCHEMA, errors=errors)

    async def async_step_reauth(self, entry_data: Mapping[str, Any]) -> ConfigFlowResult:
        """The feed link was revoked or regenerated in Bloomery."""
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        return await self._update_url("reauth_confirm", user_input, self._get_reauth_entry)

    async def async_step_reconfigure(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        return await self._update_url("reconfigure", user_input, self._get_reconfigure_entry)

    async def _update_url(self, step_id: str, user_input: dict[str, Any] | None, get_entry: Any) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input:
            url, _data, errors = await self._validate(user_input)
            if url:
                self._abort_if_unique_id_mismatch()
                return self.async_update_reload_and_abort(get_entry(), data_updates={CONF_URL: url})
        return self.async_show_form(step_id=step_id, data_schema=SCHEMA, errors=errors)
