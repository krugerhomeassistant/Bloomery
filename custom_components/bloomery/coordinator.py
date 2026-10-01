"""Polling coordinator for Bloomery."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_URL
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import BloomeryAuthError, BloomeryClient, BloomeryConnectionError
from .const import DOMAIN, UPDATE_INTERVAL

_LOGGER = logging.getLogger(__name__)

type BloomeryConfigEntry = ConfigEntry[BloomeryCoordinator]


class BloomeryCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Fetches the whole feed every 15 minutes (and right after midnight, see __init__)."""

    config_entry: BloomeryConfigEntry

    def __init__(self, hass: HomeAssistant, entry: BloomeryConfigEntry) -> None:
        super().__init__(
            hass, _LOGGER, name=DOMAIN, config_entry=entry, update_interval=UPDATE_INTERVAL, always_update=False
        )
        self.client = BloomeryClient(async_get_clientsession(hass), entry.data[CONF_URL], hass.config.time_zone)

    async def _async_update_data(self) -> dict[str, Any]:
        try:
            return await self.client.async_get_state()
        except BloomeryAuthError as err:
            raise ConfigEntryAuthFailed(translation_domain=DOMAIN, translation_key="feed_revoked") from err
        except BloomeryConnectionError as err:
            raise UpdateFailed(
                translation_domain=DOMAIN,
                translation_key="cannot_connect",
                translation_placeholders={"error": str(err)},
            ) from err
