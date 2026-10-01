"""Config, reauth and reconfigure flows."""

from typing import Any

from aiohttp import ClientError
from homeassistant.config_entries import SOURCE_USER
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from pytest_homeassistant_custom_component.common import MockConfigEntry
from pytest_homeassistant_custom_component.test_util.aiohttp import AiohttpClientMocker

from .conftest import URL

NEW = "http://bloomery.local:8420/api/ha/newtokennewtoken"


async def test_user_flow(hass: HomeAssistant, aioclient_mock: AiohttpClientMocker, feed: dict[str, Any]) -> None:
    r = await hass.config_entries.flow.async_init("bloomery", context={"source": SOURCE_USER})
    assert r["type"] is FlowResultType.FORM

    r = await hass.config_entries.flow.async_configure(r["flow_id"], {"url": "http://x/nope"})
    assert r["errors"] == {"url": "invalid_url"}

    aioclient_mock.get("http://bloomery.local:8420/api/ha/gonegonegone", status=404)
    r = await hass.config_entries.flow.async_configure(
        r["flow_id"], {"url": "http://bloomery.local:8420/api/ha/gonegonegone"}
    )
    assert r["errors"] == {"url": "invalid_token"}

    aioclient_mock.get("http://down.local/api/ha/abcdefghijkl", exc=ClientError())
    r = await hass.config_entries.flow.async_configure(r["flow_id"], {"url": "http://down.local/api/ha/abcdefghijkl"})
    assert r["errors"] == {"base": "cannot_connect"}

    aioclient_mock.get(URL, json=feed)
    r = await hass.config_entries.flow.async_configure(r["flow_id"], {"url": f" {URL}/?tz=UTC "})
    assert r["type"] is FlowResultType.CREATE_ENTRY
    assert r["title"] == "Bloomery (Mia)" and r["data"] == {"url": URL}
    assert r["result"].unique_id == "bloomery.local:8420_1"
    assert aioclient_mock.mock_calls[-1][1].query["tz"] == hass.config.time_zone


async def test_duplicate_aborts(
    hass: HomeAssistant, setup: MockConfigEntry, aioclient_mock: AiohttpClientMocker, feed: dict[str, Any]
) -> None:
    aioclient_mock.get(NEW, json=feed)
    r = await hass.config_entries.flow.async_init("bloomery", context={"source": SOURCE_USER})
    r = await hass.config_entries.flow.async_configure(r["flow_id"], {"url": NEW})
    assert r["type"] is FlowResultType.ABORT and r["reason"] == "already_configured"
    assert setup.data["url"] == NEW  # same account, newer link wins


async def test_reconfigure(
    hass: HomeAssistant, setup: MockConfigEntry, aioclient_mock: AiohttpClientMocker, feed: dict[str, Any]
) -> None:
    aioclient_mock.get(NEW, json=feed)
    r = await setup.start_reconfigure_flow(hass)
    r = await hass.config_entries.flow.async_configure(r["flow_id"], {"url": "bad"})
    assert r["errors"] == {"url": "invalid_url"}
    r = await hass.config_entries.flow.async_configure(r["flow_id"], {"url": NEW})
    assert r["reason"] == "reconfigure_successful" and setup.data["url"] == NEW


async def test_reconfigure_other_account(
    hass: HomeAssistant, setup: MockConfigEntry, aioclient_mock: AiohttpClientMocker, feed: dict[str, Any]
) -> None:
    aioclient_mock.get(NEW, json={**feed, "user_id": 2})
    r = await setup.start_reconfigure_flow(hass)
    r = await hass.config_entries.flow.async_configure(r["flow_id"], {"url": NEW})
    assert r["reason"] == "unique_id_mismatch" and setup.data["url"] == URL


async def test_reauth(
    hass: HomeAssistant, setup: MockConfigEntry, aioclient_mock: AiohttpClientMocker, feed: dict[str, Any]
) -> None:
    aioclient_mock.get(NEW, json=feed)
    r = await setup.start_reauth_flow(hass)
    assert r["step_id"] == "reauth_confirm"
    r = await hass.config_entries.flow.async_configure(r["flow_id"], {"url": NEW})
    assert r["reason"] == "reauth_successful" and setup.data["url"] == NEW
