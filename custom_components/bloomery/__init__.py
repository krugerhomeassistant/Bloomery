"""Bloomery: cycle sensors and calendars from a self-hosted Bloomery server."""

from __future__ import annotations

from datetime import datetime

from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.event import async_track_time_change

from .coordinator import BloomeryConfigEntry, BloomeryCoordinator

PLATFORMS = [Platform.BINARY_SENSOR, Platform.CALENDAR, Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: BloomeryConfigEntry) -> bool:
    """Set up Bloomery from a config entry."""
    coordinator = BloomeryCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator

    async def _new_day(_now: datetime) -> None:  # cycle day changes at local midnight
        await coordinator.async_request_refresh()

    entry.async_on_unload(async_track_time_change(hass, _new_day, hour=0, minute=0, second=10))
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: BloomeryConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
