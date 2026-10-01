"""Diagnostics for Bloomery (feed URL contains the access token, so it's redacted)."""

from __future__ import annotations

from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.const import CONF_URL
from homeassistant.core import HomeAssistant

from .coordinator import BloomeryConfigEntry

TO_REDACT = {CONF_URL, "name", "unique_id", "title"}


async def async_get_config_entry_diagnostics(hass: HomeAssistant, entry: BloomeryConfigEntry) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    coordinator = entry.runtime_data
    return {
        "entry": async_redact_data(entry.as_dict(), TO_REDACT),
        "last_update_success": coordinator.last_update_success,
        "data": async_redact_data(coordinator.data, TO_REDACT),
    }
