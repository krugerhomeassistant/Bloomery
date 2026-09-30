from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import date
from typing import Any

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorEntityDescription
from homeassistant.const import EntityCategory, UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import BloomeryConfigEntry, BloomeryEntity


def _date(key: str) -> Callable[[dict], date | None]:
    return lambda d: date.fromisoformat(d[key]) if d.get(key) else None


@dataclass(frozen=True, kw_only=True)
class BloomerySensorDescription(SensorEntityDescription):
    value: Callable[[dict], Any]
    attrs: Callable[[dict], dict] | None = None


DAYS = {"device_class": SensorDeviceClass.DURATION, "native_unit_of_measurement": UnitOfTime.DAYS}
SENSORS = (
    BloomerySensorDescription(key="status", value=lambda d: f"{d.get('label') or ''} {d.get('headline') or ''}".strip() or None,
                              attrs=lambda d: {"summary": d.get("summary"), "state": d.get("state")}),
    BloomerySensorDescription(key="cycle_day", value=lambda d: d.get("cycle_day")),
    BloomerySensorDescription(key="phase", device_class=SensorDeviceClass.ENUM,
                              options=["menstrual", "follicular", "fertile", "ovulation", "luteal"], value=lambda d: d.get("phase")),
    BloomerySensorDescription(key="days_until_period", value=lambda d: d.get("days_until_period"), **DAYS),
    BloomerySensorDescription(key="next_period", device_class=SensorDeviceClass.DATE, value=_date("next_period")),
    BloomerySensorDescription(key="ovulation", device_class=SensorDeviceClass.DATE, value=_date("ovulation")),
    BloomerySensorDescription(key="pregnancy_chance", device_class=SensorDeviceClass.ENUM,
                              options=["low", "medium", "high"], value=lambda d: d.get("pregnancy_chance")),
    BloomerySensorDescription(key="life_stage", device_class=SensorDeviceClass.ENUM,
                              options=["cycle", "pregnancy", "perimenopause"], value=lambda d: d.get("mode")),
    BloomerySensorDescription(key="pregnancy_week", value=lambda d: d.get("pregnancy_week")),
    BloomerySensorDescription(key="due_date", device_class=SensorDeviceClass.DATE, value=_date("due_date")),
    BloomerySensorDescription(key="cycle_length", entity_category=EntityCategory.DIAGNOSTIC, value=lambda d: d.get("cycle_length"), **DAYS),
    BloomerySensorDescription(key="period_length", entity_category=EntityCategory.DIAGNOSTIC, value=lambda d: d.get("period_length"), **DAYS),
)


async def async_setup_entry(hass: HomeAssistant, entry: BloomeryConfigEntry, add: AddConfigEntryEntitiesCallback) -> None:
    add(BloomerySensor(entry.runtime_data, desc) for desc in SENSORS)


class BloomerySensor(BloomeryEntity, SensorEntity):
    entity_description: BloomerySensorDescription

    def __init__(self, coordinator, desc: BloomerySensorDescription) -> None:
        super().__init__(coordinator, desc.key)
        self.entity_description = desc

    @property
    def native_value(self) -> Any:
        return self.entity_description.value(self.coordinator.data)

    @property
    def extra_state_attributes(self) -> dict | None:
        a = self.entity_description.attrs
        return a(self.coordinator.data) if a else None
