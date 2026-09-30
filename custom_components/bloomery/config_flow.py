from __future__ import annotations

from typing import Any
from urllib.parse import urlparse

import voluptuous as vol
from aiohttp import ClientError

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_URL

from . import DOMAIN, FEED_RE, FeedGone, fetch

SCHEMA = vol.Schema({vol.Required(CONF_URL): str})


class BloomeryConfigFlow(ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def _validate(self, user_input: dict[str, Any]) -> tuple[dict | None, dict[str, str]]:
        url = user_input[CONF_URL].strip()
        if not FEED_RE.match(url):
            return None, {CONF_URL: "invalid_url"}
        try:
            data = await fetch(self.hass, url.split("?")[0])
        except FeedGone:
            return None, {CONF_URL: "invalid_token"}
        except (ClientError, TimeoutError, ValueError):
            return None, {"base": "cannot_connect"}
        return data, {}

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input:
            data, errors = await self._validate(user_input)
            if data:
                url = user_input[CONF_URL].strip().split("?")[0]
                # stable per Bloomery user, so a regenerated link keeps the same entities
                await self.async_set_unique_id(f"{urlparse(url).netloc}_{data['user_id']}")
                self._abort_if_unique_id_configured(updates={CONF_URL: url})
                return self.async_create_entry(title=f"Bloomery ({data['name']})", data={CONF_URL: url})
        return self.async_show_form(step_id="user", data_schema=SCHEMA, errors=errors)

    async def async_step_reconfigure(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input:
            data, errors = await self._validate(user_input)
            if data:
                url = user_input[CONF_URL].strip().split("?")[0]
                await self.async_set_unique_id(f"{urlparse(url).netloc}_{data['user_id']}")
                self._abort_if_unique_id_mismatch()
                return self.async_update_reload_and_abort(self._get_reconfigure_entry(), data_updates={CONF_URL: url})
        return self.async_show_form(step_id="reconfigure", data_schema=SCHEMA, errors=errors)
