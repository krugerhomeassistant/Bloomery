"""Bloomery: cycle sensors from a self-hosted Bloomery server (read-only feed URL)."""
from __future__ import annotations

import logging
import re
from datetime import timedelta

from aiohttp import ClientError, ClientTimeout

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_URL, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.event import async_track_time_change
from homeassistant.helpers.update_coordinator import CoordinatorEntity, DataUpdateCoordinator, UpdateFailed

DOMAIN = "bloomery"
PLATFORMS = [Platform.SENSOR, Platform.BINARY_SENSOR]
FEED_RE = re.compile(r"^(https?://[^?#]+?)/api/ha/([A-Za-z0-9_-]{8,})/?(?:[?#].*)?$")
_LOGGER = logging.getLogger(__name__)

type BloomeryConfigEntry = ConfigEntry[BloomeryCoordinator]


class FeedGone(Exception):
    """Token revoked or regenerated in Bloomery."""


async def fetch(hass: HomeAssistant, url: str) -> dict:
    async with async_get_clientsession(hass).get(
        url, params={"tz": hass.config.time_zone}, timeout=ClientTimeout(total=15)
    ) as r:
        if r.status == 404:
            raise FeedGone
        r.raise_for_status()
        return await r.json()


class BloomeryCoordinator(DataUpdateCoordinator[dict]):
    def __init__(self, hass: HomeAssistant, entry: BloomeryConfigEntry) -> None:
        super().__init__(hass, _LOGGER, name=DOMAIN, config_entry=entry,
                         update_interval=timedelta(minutes=15), always_update=False)
        self.url = entry.data[CONF_URL]

    async def _async_update_data(self) -> dict:
        try:
            return await fetch(self.hass, self.url)
        except FeedGone as err:
            raise UpdateFailed("Feed link no longer active: create a new one in Bloomery and reconfigure") from err
        except (ClientError, TimeoutError) as err:
            raise UpdateFailed(f"Can't reach Bloomery: {err}") from err


async def async_setup_entry(hass: HomeAssistant, entry: BloomeryConfigEntry) -> bool:
    coordinator = BloomeryCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator
    # a new cycle day starts at midnight; don't wait up to 15 min for it
    entry.async_on_unload(async_track_time_change(
        hass, lambda _now: hass.async_create_task(coordinator.async_request_refresh()), hour=0, minute=0, second=10))
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: BloomeryConfigEntry) -> bool:
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


class BloomeryEntity(CoordinatorEntity[BloomeryCoordinator]):
    _attr_has_entity_name = True

    def __init__(self, coordinator: BloomeryCoordinator, key: str) -> None:
        super().__init__(coordinator)
        entry = coordinator.config_entry
        self._attr_translation_key = key
        self._attr_unique_id = f"{entry.unique_id}_{key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.unique_id)}, name=f"Bloomery {coordinator.data.get('name', '')}".strip(),
            manufacturer="Bloomery", model="Cycle tracker", sw_version=coordinator.data.get("version"),
            configuration_url=FEED_RE.match(coordinator.url).group(1),
        )
