"""Options flow (API key) and the logging actions."""

from typing import Any

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError, ServiceValidationError
from pytest_homeassistant_custom_component.common import MockConfigEntry
from pytest_homeassistant_custom_component.test_util.aiohttp import AiohttpClientMocker

from .conftest import URL

QUICK = "http://bloomery.local:8420/api/quick"


async def test_options_flow(hass: HomeAssistant, setup: MockConfigEntry, aioclient_mock: AiohttpClientMocker) -> None:
    aioclient_mock.get(f"{QUICK}/catalog", status=401)
    r = await hass.config_entries.options.async_init(setup.entry_id)
    r = await hass.config_entries.options.async_configure(r["flow_id"], {"api_key": "bad"})
    assert r["errors"] == {"api_key": "invalid_api_key"}

    aioclient_mock.clear_requests()
    aioclient_mock.get(f"{QUICK}/catalog", exc=TimeoutError())
    r = await hass.config_entries.options.async_configure(r["flow_id"], {"api_key": "key"})
    assert r["errors"] == {"base": "cannot_connect"}

    aioclient_mock.clear_requests()
    aioclient_mock.get(f"{QUICK}/catalog", json={"categories": []})
    r = await hass.config_entries.options.async_configure(r["flow_id"], {"api_key": " key "})
    assert r["type"] == "create_entry" and setup.options == {"api_key": "key"}
    assert aioclient_mock.mock_calls[-1][3]["Authorization"] == "Bearer key"

    r = await hass.config_entries.options.async_init(setup.entry_id)  # clearing turns actions off
    await hass.config_entries.options.async_configure(r["flow_id"], {})
    assert setup.options == {"api_key": ""}


async def _with_key(hass: HomeAssistant, entry: MockConfigEntry) -> None:
    hass.config_entries.async_update_entry(entry, options={"api_key": "key"})
    await hass.async_block_till_done()


async def test_actions(hass: HomeAssistant, setup: MockConfigEntry, aioclient_mock: AiohttpClientMocker,
                       feed: dict[str, Any]) -> None:
    eid = setup.entry_id
    with pytest.raises(ServiceValidationError, match="API key"):
        await hass.services.async_call("bloomery", "log_period_start", {"config_entry_id": eid}, blocking=True)
    with pytest.raises(ServiceValidationError):
        await hass.services.async_call("bloomery", "log", {"config_entry_id": "nope"}, blocking=True)
    await _with_key(hass, setup)

    aioclient_mock.post(f"{QUICK}/period-start", json={"ok": True, "date": "2026-10-06", "days": 5})
    aioclient_mock.post(f"{QUICK}/log", json={"ok": True, "date": "2026-10-05", "logged": ["Cramps", "Sad"]})
    calls_before = aioclient_mock.call_count
    r = await hass.services.async_call("bloomery", "log_period_start", {"config_entry_id": eid}, blocking=True,
                                       return_response=True)
    assert r == {"ok": True, "date": "2026-10-06", "days": 5}
    sent = aioclient_mock.mock_calls[calls_before]
    assert sent[3]["Authorization"] == "Bearer key" and sent[2] == {"tz": hass.config.time_zone}

    r = await hass.services.async_call(
        "bloomery", "log",
        {"config_entry_id": eid, "items": ["cramps", "mood:sad"], "flow": "heavy", "temperature": 36.55,
         "note": "hi", "date": "2026-10-05"},
        blocking=True, return_response=True)
    assert r["logged"] == ["Cramps", "Sad"]
    body = [c for c in aioclient_mock.mock_calls if str(c[1]).endswith("/log")][-1][2]
    assert body == {"tz": hass.config.time_zone, "tags": ["cramps", "mood:sad"], "flow": "heavy",
                    "temperature": 36.55, "note": "hi", "day": "2026-10-05"}


@pytest.mark.parametrize(
    ("mock", "error", "match"),
    [({"status": 401}, HomeAssistantError, "rejected the API key"),
     ({"status": 422, "json": {"detail": "Unknown: unicorns"}}, ServiceValidationError, "unicorns"),
     ({"exc": TimeoutError()}, HomeAssistantError, "reach Bloomery")],
)
async def test_action_errors(hass: HomeAssistant, setup: MockConfigEntry, aioclient_mock: AiohttpClientMocker,
                             mock: dict[str, Any], error: type[Exception], match: str) -> None:
    await _with_key(hass, setup)
    aioclient_mock.post(f"{QUICK}/log", **mock)
    with pytest.raises(error, match=match):
        await hass.services.async_call("bloomery", "log", {"config_entry_id": setup.entry_id, "items": ["unicorns"]},
                                       blocking=True)
