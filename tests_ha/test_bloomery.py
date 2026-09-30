"""Run: pip install pytest-homeassistant-custom-component && pytest tests_ha (Python 3.13+)."""
from homeassistant.config_entries import SOURCE_RECONFIGURE, SOURCE_USER
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

URL = "http://bloomery.local:8420/api/ha/abcdefghijkl"
FEED = {"user_id": 1, "name": "Mia", "version": "1.1.0", "mode": "cycle", "pregnancy_week": None, "due_date": None,
        "state": "fertile", "label": "Ovulation in", "headline": "3 days", "summary": "Medium chance",
        "cycle_day": 13, "phase": "fertile", "pregnancy_chance": "medium", "in_period": False, "fertile": True,
        "days_until_period": 17, "next_period": "2026-10-17", "ovulation": "2026-10-03",
        "cycle_length": 29, "period_length": 4, "today": "2026-09-30"}


async def test_flow_and_entities(hass: HomeAssistant, aioclient_mock) -> None:
    r = await hass.config_entries.flow.async_init("bloomery", context={"source": SOURCE_USER})
    r = await hass.config_entries.flow.async_configure(r["flow_id"], {"url": "http://x/nope"})
    assert r["errors"] == {"url": "invalid_url"}

    aioclient_mock.get("http://bloomery.local:8420/api/ha/gonegonegone", status=404)
    r = await hass.config_entries.flow.async_configure(r["flow_id"], {"url": "http://bloomery.local:8420/api/ha/gonegonegone"})
    assert r["errors"] == {"url": "invalid_token"}

    aioclient_mock.get(URL, json=FEED)
    r = await hass.config_entries.flow.async_configure(r["flow_id"], {"url": URL + "?tz=UTC"})
    assert r["type"] is FlowResultType.CREATE_ENTRY and r["title"] == "Bloomery (Mia)" and r["data"] == {"url": URL}
    await hass.async_block_till_done()

    s = lambda e: hass.states.get(e).state
    assert s("sensor.bloomery_mia_cycle_day") == "13"
    assert s("sensor.bloomery_mia_phase") == "fertile"
    assert s("sensor.bloomery_mia_status") == "Ovulation in 3 days"
    assert s("sensor.bloomery_mia_next_period") == "2026-10-17"
    assert s("sensor.bloomery_mia_days_until_period") == "17"
    assert s("sensor.bloomery_mia_due_date") == "unknown"
    assert s("binary_sensor.bloomery_mia_fertile_window") == "on"
    assert s("binary_sensor.bloomery_mia_period") == "off"
    assert aioclient_mock.mock_calls[-1][1].query["tz"] == hass.config.time_zone

    # same account again -> abort
    r = await hass.config_entries.flow.async_init("bloomery", context={"source": SOURCE_USER})
    r = await hass.config_entries.flow.async_configure(r["flow_id"], {"url": URL})
    assert r["type"] is FlowResultType.ABORT and r["reason"] == "already_configured"

    # regenerated token -> reconfigure keeps the entry
    entry = hass.config_entries.async_entries("bloomery")[0]
    new = "http://bloomery.local:8420/api/ha/newtokennewtoken"
    aioclient_mock.get(new, json=FEED)
    r = await hass.config_entries.flow.async_init("bloomery", context={"source": SOURCE_RECONFIGURE, "entry_id": entry.entry_id})
    r = await hass.config_entries.flow.async_configure(r["flow_id"], {"url": new})
    assert r["reason"] == "reconfigure_successful" and entry.data["url"] == new
