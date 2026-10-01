"""Calendars for Bloomery: one per event type so each gets its own colour."""

from __future__ import annotations

from datetime import date, datetime, timedelta

from homeassistant.components.calendar import CalendarEntity, CalendarEvent
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.util import dt as dt_util

from .coordinator import BloomeryConfigEntry, BloomeryCoordinator
from .entity import BloomeryEntity

PARALLEL_UPDATES = 0

# calendar key -> (feed event kind, default colour matching the Bloomery app; users can change it per calendar)
CALENDARS = {
    "periods": ("period", "#FF4A7D"),
    "fertile_windows": ("fertile", "#3CC4BB"),
    "ovulation_days": ("ovulation", "#7C5CE0"),
}


async def async_setup_entry(
    hass: HomeAssistant, entry: BloomeryConfigEntry, async_add_entities: AddConfigEntryEntitiesCallback
) -> None:
    """Set up Bloomery calendars."""
    async_add_entities(BloomeryCalendar(entry.runtime_data, key) for key in CALENDARS)


class BloomeryCalendar(BloomeryEntity, CalendarEntity):
    """All-day events of one kind (e.g. logged and predicted periods)."""

    def __init__(self, coordinator: BloomeryCoordinator, key: str) -> None:
        super().__init__(coordinator, key)
        self._kind, self._attr_initial_color = CALENDARS[key]

    def _events(self) -> list[CalendarEvent]:
        return [
            CalendarEvent(
                start=date.fromisoformat(e["start"]),
                end=date.fromisoformat(e["end"]) + timedelta(days=1),
                summary=e["title"],
                uid=f"{e['kind']}-{e['start']}",
            )
            for e in self.coordinator.data.get("events", [])
            if e["kind"] == self._kind
        ]

    @property
    def event(self) -> CalendarEvent | None:
        """The current or next event."""
        today = dt_util.now().date()
        return next((e for e in self._events() if e.end > today), None)

    async def async_get_events(
        self, hass: HomeAssistant, start_date: datetime, end_date: datetime
    ) -> list[CalendarEvent]:
        """Events overlapping the requested range."""
        start, end = dt_util.as_local(start_date).date(), dt_util.as_local(end_date).date()
        return [e for e in self._events() if e.start < end and e.end > start]
