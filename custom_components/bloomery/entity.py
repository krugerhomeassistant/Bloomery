"""Base entity for Bloomery."""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import BloomeryCoordinator


class BloomeryEntity(CoordinatorEntity[BloomeryCoordinator]):
    """All entities belong to one service device per Bloomery account."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: BloomeryCoordinator, key: str) -> None:
        super().__init__(coordinator)
        unique_id = coordinator.config_entry.unique_id
        assert unique_id is not None
        self._attr_translation_key = key
        self._attr_unique_id = f"{unique_id}_{key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, unique_id)},
            entry_type=DeviceEntryType.SERVICE,
            name=f"Bloomery {coordinator.data.get('name', '')}".strip(),
            manufacturer="Bloomery",
            model="Cycle tracker",
            sw_version=coordinator.data.get("version"),
            configuration_url=coordinator.client.base_url,
        )
