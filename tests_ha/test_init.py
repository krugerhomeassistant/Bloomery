"""Setup, entities, calendars, refresh behaviour and diagnostics."""

from datetime import timedelta
from typing import Any

from aiohttp import ClientError
from freezegun.api import FrozenDateTimeFactory
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er
from homeassistant.util import dt as dt_util
from pytest_homeassistant_custom_component.common import MockConfigEntry, async_fire_time_changed
from pytest_homeassistant_custom_component.test_util.aiohttp import AiohttpClientMocker

from custom_components.bloomery.diagnostics import async_get_config_entry_diagnostics

from .conftest import URL


async def test_entities(
    hass: HomeAssistant, setup: MockConfigEntry, entity_registry: er.EntityRegistry, device_registry: dr.DeviceRegistry
) -> None:
    s = lambda e: hass.states.get(e).state
    assert s("sensor.bloomery_mia_cycle_day") == "13"
    assert s("sensor.bloomery_mia_phase") == "fertile"
    assert s("sensor.bloomery_mia_status") == "Ovulation in 3 days"
    assert hass.states.get("sensor.bloomery_mia_status").attributes["summary"] == "Medium chance"
    assert s("sensor.bloomery_mia_next_period") == "2026-10-17"
    assert s("sensor.bloomery_mia_days_until_period") == "17"
    assert s("sensor.bloomery_mia_life_stage") == "cycle"
    assert s("binary_sensor.bloomery_mia_fertile_window") == "on"
    assert s("binary_sensor.bloomery_mia_period") == "off"
    assert hass.states.get("sensor.bloomery_mia_due_date") is None  # disabled by default
    assert entity_registry.async_get("sensor.bloomery_mia_due_date").disabled_by is er.RegistryEntryDisabler.INTEGRATION
    assert entity_registry.async_get("calendar.bloomery_mia_periods").options["calendar"]["color"] == "#FF4A7D"
    device = device_registry.async_get_device(identifiers={("bloomery", "bloomery.local:8420_1")})
    assert device.name == "Bloomery Mia" and device.sw_version == "1.2.0"
    assert device.configuration_url == "http://bloomery.local:8420"


async def test_calendars(
    hass: HomeAssistant,
    entry: MockConfigEntry,
    aioclient_mock: AiohttpClientMocker,
    feed: dict[str, Any],
    freezer: FrozenDateTimeFactory,
) -> None:
    freezer.move_to("2026-09-30 12:00:00+00:00")  # inside the sample fertile window, before setup writes states
    aioclient_mock.get(URL, json=feed)
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    periods = hass.states.get("calendar.bloomery_mia_periods")
    assert periods.attributes["message"] == "Predicted period" and periods.state == "off"
    assert hass.states.get("calendar.bloomery_mia_fertile_windows").state == "on"
    r = await hass.services.async_call(
        "calendar",
        "get_events",
        {
            "entity_id": ["calendar.bloomery_mia_periods", "calendar.bloomery_mia_ovulation"],
            "start_date_time": "2026-09-01T00:00:00",
            "end_date_time": "2026-10-31T00:00:00",
        },
        blocking=True,
        return_response=True,
    )
    assert [e["summary"] for e in r["calendar.bloomery_mia_periods"]["events"]] == ["Period", "Predicted period"]
    assert r["calendar.bloomery_mia_periods"]["events"][0] | {} == {
        "start": "2026-09-18",
        "end": "2026-09-22",
        "summary": "Period",
    }
    assert len(r["calendar.bloomery_mia_ovulation"]["events"]) == 1


async def test_unavailable_then_recovers(
    hass: HomeAssistant,
    setup: MockConfigEntry,
    aioclient_mock: AiohttpClientMocker,
    feed: dict[str, Any],
    freezer: FrozenDateTimeFactory,
) -> None:
    aioclient_mock.clear_requests()
    aioclient_mock.get(URL, exc=ClientError("boom"))
    freezer.tick(timedelta(minutes=16))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()
    assert hass.states.get("sensor.bloomery_mia_cycle_day").state == "unavailable"

    aioclient_mock.clear_requests()
    aioclient_mock.get(URL, json={**feed, "cycle_day": 14, "in_period": None})
    freezer.tick(timedelta(minutes=16))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()
    assert hass.states.get("sensor.bloomery_mia_cycle_day").state == "14"
    assert hass.states.get("binary_sensor.bloomery_mia_period").state == "unknown"


async def test_revoked_link_starts_reauth(
    hass: HomeAssistant, setup: MockConfigEntry, aioclient_mock: AiohttpClientMocker, freezer: FrozenDateTimeFactory
) -> None:
    aioclient_mock.clear_requests()
    aioclient_mock.get(URL, status=404)
    freezer.tick(timedelta(minutes=16))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()
    flows = hass.config_entries.flow.async_progress()
    assert [f["context"]["source"] for f in flows] == ["reauth"]


async def test_midnight_refresh(
    hass: HomeAssistant, setup: MockConfigEntry, aioclient_mock: AiohttpClientMocker, freezer: FrozenDateTimeFactory
) -> None:
    calls = aioclient_mock.call_count
    now = dt_util.now()
    freezer.move_to((now + timedelta(days=1)).replace(hour=0, minute=0, second=11))  # next local midnight
    async_fire_time_changed(hass)
    await hass.async_block_till_done()
    assert aioclient_mock.call_count > calls


async def test_setup_retry_when_down(
    hass: HomeAssistant, entry: MockConfigEntry, aioclient_mock: AiohttpClientMocker
) -> None:
    aioclient_mock.get(URL, exc=TimeoutError())
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    assert entry.state is ConfigEntryState.SETUP_RETRY


async def test_unload(hass: HomeAssistant, setup: MockConfigEntry) -> None:
    assert await hass.config_entries.async_unload(setup.entry_id)
    assert setup.state is ConfigEntryState.NOT_LOADED


async def test_diagnostics_redacts_token(hass: HomeAssistant, setup: MockConfigEntry) -> None:
    d = await async_get_config_entry_diagnostics(hass, setup)
    text = str(d)
    assert "abcdefghijkl" not in text and "Mia" not in text
    assert d["data"]["cycle_day"] == 13 and d["last_update_success"] is True
