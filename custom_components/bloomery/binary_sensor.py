"""Binary sensors for Bloomery."""

from __future__ import annotations

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import BloomeryConfigEntry, BloomeryCoordinator
from .entity import BloomeryEntity

PARALLEL_UPDATES = 0

FEED_KEYS = {"period": "in_period", "fertile_window": "fertile"}


async def async_setup_entry(
    hass: HomeAssistant, entry: BloomeryConfigEntry, async_add_entities: AddConfigEntryEntitiesCallback
) -> None:
    """Set up Bloomery binary sensors."""
    async_add_entities(BloomeryBinarySensor(entry.runtime_data, key) for key in FEED_KEYS)


class BloomeryBinarySensor(BloomeryEntity, BinarySensorEntity):
    """On during a period / the fertile window."""

    def __init__(self, coordinator: BloomeryCoordinator, key: str) -> None:
        super().__init__(coordinator, key)
        self._feed_key = FEED_KEYS[key]

    @property
    def is_on(self) -> bool | None:
        value = self.coordinator.data.get(self._feed_key)
        return None if value is None else bool(value)
