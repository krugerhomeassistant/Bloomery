"""Sensors for Bloomery."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import date
from typing import Any

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorEntityDescription
from homeassistant.const import EntityCategory, UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import BloomeryConfigEntry, BloomeryCoordinator
from .entity import BloomeryEntity

PARALLEL_UPDATES = 0  # coordinator-based, read-only


def _date(key: str) -> Callable[[dict[str, Any]], date | None]:
    return lambda d: date.fromisoformat(d[key]) if d.get(key) else None


def _status(d: dict[str, Any]) -> str | None:
    return f"{d.get('label') or ''} {d.get('headline') or ''}".strip() or None


@dataclass(frozen=True, kw_only=True)
class BloomerySensorDescription(SensorEntityDescription):
    """Sensor description with a value getter over the feed JSON."""

    value: Callable[[dict[str, Any]], Any]
    attrs: Callable[[dict[str, Any]], dict[str, Any]] | None = None


DAYS: dict[str, Any] = {"device_class": SensorDeviceClass.DURATION, "native_unit_of_measurement": UnitOfTime.DAYS}
SENSORS: tuple[BloomerySensorDescription, ...] = (
    BloomerySensorDescription(
        key="status", value=_status, attrs=lambda d: {"summary": d.get("summary"), "state": d.get("state")}
    ),
    BloomerySensorDescription(key="cycle_day", value=lambda d: d.get("cycle_day")),
    BloomerySensorDescription(
        key="phase",
        device_class=SensorDeviceClass.ENUM,
        options=["menstrual", "follicular", "fertile", "ovulation", "luteal"],
        value=lambda d: d.get("phase"),
    ),
    BloomerySensorDescription(key="days_until_period", value=lambda d: d.get("days_until_period"), **DAYS),
    BloomerySensorDescription(key="next_period", device_class=SensorDeviceClass.DATE, value=_date("next_period")),
    BloomerySensorDescription(key="ovulation", device_class=SensorDeviceClass.DATE, value=_date("ovulation")),
    BloomerySensorDescription(
        key="pregnancy_chance",
        device_class=SensorDeviceClass.ENUM,
        options=["low", "medium", "high"],
        value=lambda d: d.get("pregnancy_chance"),
    ),
    BloomerySensorDescription(
        key="life_stage",
        device_class=SensorDeviceClass.ENUM,
        options=["cycle", "pregnancy", "perimenopause"],
        value=lambda d: d.get("mode"),
    ),
    BloomerySensorDescription(
        key="pregnancy_week", entity_registry_enabled_default=False, value=lambda d: d.get("pregnancy_week")
    ),
    BloomerySensorDescription(
        key="due_date",
        device_class=SensorDeviceClass.DATE,
        entity_registry_enabled_default=False,
        value=_date("due_date"),
    ),
    BloomerySensorDescription(
        key="cycle_length", entity_category=EntityCategory.DIAGNOSTIC, value=lambda d: d.get("cycle_length"), **DAYS
    ),
    BloomerySensorDescription(
        key="period_length", entity_category=EntityCategory.DIAGNOSTIC, value=lambda d: d.get("period_length"), **DAYS
    ),
)


async def async_setup_entry(
    hass: HomeAssistant, entry: BloomeryConfigEntry, async_add_entities: AddConfigEntryEntitiesCallback
) -> None:
    """Set up Bloomery sensors."""
    async_add_entities(BloomerySensor(entry.runtime_data, desc) for desc in SENSORS)


class BloomerySensor(BloomeryEntity, SensorEntity):
    """A value from the Bloomery feed."""

    entity_description: BloomerySensorDescription

    def __init__(self, coordinator: BloomeryCoordinator, description: BloomerySensorDescription) -> None:
        super().__init__(coordinator, description.key)
        self.entity_description = description

    @property
    def native_value(self) -> Any:
        return self.entity_description.value(self.coordinator.data)

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        attrs = self.entity_description.attrs
        return attrs(self.coordinator.data) if attrs else None
