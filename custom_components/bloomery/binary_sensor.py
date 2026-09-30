from __future__ import annotations

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import BloomeryConfigEntry, BloomeryEntity

KEYS = {"period": "in_period", "fertile_window": "fertile"}


async def async_setup_entry(hass: HomeAssistant, entry: BloomeryConfigEntry, add: AddConfigEntryEntitiesCallback) -> None:
    add(BloomeryBinary(entry.runtime_data, key) for key in KEYS)


class BloomeryBinary(BloomeryEntity, BinarySensorEntity):
    @property
    def is_on(self) -> bool | None:
        return self.coordinator.data.get(KEYS[self._attr_translation_key])
