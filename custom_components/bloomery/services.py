"""Actions: log a period start, or symptoms / mood / flow / temperature / a note, in Bloomery (needs the API key)."""

from __future__ import annotations

from datetime import date
from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant, ServiceCall, ServiceResponse, SupportsResponse
from homeassistant.exceptions import HomeAssistantError, ServiceValidationError
from homeassistant.helpers import config_validation as cv

from .api import BloomeryConnectionError, BloomeryKeyError, BloomeryRejected
from .const import CONF_API_KEY, DOMAIN
from .coordinator import BloomeryConfigEntry

ATTR_ENTRY = "config_entry_id"
BASE = {vol.Required(ATTR_ENTRY): cv.string, vol.Optional("date"): cv.date}
SCHEMAS = {
    "log_period_start": vol.Schema(BASE),
    "log": vol.Schema(
        {
            **BASE,
            vol.Optional("items"): vol.All(cv.ensure_list, [cv.string]),
            vol.Optional("flow"): vol.In(["spotting", "light", "medium", "heavy"]),
            vol.Optional("temperature"): vol.All(vol.Coerce(float), vol.Range(min=32, max=43)),
            vol.Optional("note"): cv.string,
        }
    ),
}


def _entry(hass: HomeAssistant, call: ServiceCall) -> BloomeryConfigEntry:
    entry: BloomeryConfigEntry | None = hass.config_entries.async_get_entry(call.data[ATTR_ENTRY])
    if not entry or entry.domain != DOMAIN or entry.state is not ConfigEntryState.LOADED:
        raise ServiceValidationError(translation_domain=DOMAIN, translation_key="entry_not_loaded")
    if not entry.options.get(CONF_API_KEY):
        raise ServiceValidationError(translation_domain=DOMAIN, translation_key="no_api_key")
    return entry


async def _call(call: ServiceCall, path: str, payload: dict[str, Any]) -> ServiceResponse:
    entry = _entry(call.hass, call)
    coordinator = entry.runtime_data
    if isinstance(day := call.data.get("date"), date):
        payload["day"] = day.isoformat()
    try:
        result = await coordinator.client.async_quick(entry.options[CONF_API_KEY], path, payload)
    except BloomeryKeyError as err:
        raise HomeAssistantError(translation_domain=DOMAIN, translation_key="invalid_api_key") from err
    except BloomeryRejected as err:
        raise ServiceValidationError(
            translation_domain=DOMAIN, translation_key="rejected", translation_placeholders={"error": str(err)}
        ) from err
    except BloomeryConnectionError as err:
        raise HomeAssistantError(
            translation_domain=DOMAIN, translation_key="cannot_connect", translation_placeholders={"error": str(err)}
        ) from err
    await coordinator.async_request_refresh()
    return result


async def _period_start(call: ServiceCall) -> ServiceResponse:
    return await _call(call, "period-start", {})


async def _log(call: ServiceCall) -> ServiceResponse:
    payload: dict[str, Any] = {"tags": call.data.get("items", [])}
    for key in ("flow", "temperature", "note"):
        if key in call.data:
            payload[key] = call.data[key]
    return await _call(call, "log", payload)


def async_setup_services(hass: HomeAssistant) -> None:
    """Register the actions (once, from async_setup)."""
    for name, handler in (("log_period_start", _period_start), ("log", _log)):
        hass.services.async_register(
            DOMAIN, name, handler, schema=SCHEMAS[name], supports_response=SupportsResponse.OPTIONAL
        )
