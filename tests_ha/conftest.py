"""Fixtures for the Bloomery integration tests (pytest-homeassistant-custom-component)."""

from collections.abc import Generator
from copy import deepcopy
from pathlib import Path
from typing import Any

import pytest
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry
from pytest_homeassistant_custom_component.test_util.aiohttp import AiohttpClientMocker

import custom_components  # the plugin's testing_config package shadows ours; add our dir to it

custom_components.__path__.append(str(Path(__file__).parents[1] / "custom_components"))

URL = "http://bloomery.local:8420/api/ha/abcdefghijkl"
FEED: dict[str, Any] = {
    "user_id": 1,
    "name": "Mia",
    "version": "1.2.0",
    "mode": "cycle",
    "pregnancy_week": None,
    "due_date": None,
    "state": "fertile",
    "label": "Ovulation in",
    "headline": "3 days",
    "summary": "Medium chance",
    "cycle_day": 13,
    "phase": "fertile",
    "pregnancy_chance": "medium",
    "in_period": False,
    "fertile": True,
    "days_until_period": 17,
    "next_period": "2026-10-17",
    "ovulation": "2026-10-03",
    "cycle_length": 29,
    "period_length": 4,
    "today": "2026-09-30",
    "events": [
        {"kind": "period", "title": "Period", "start": "2026-09-18", "end": "2026-09-21"},
        {"kind": "fertile", "title": "Fertile window", "start": "2026-09-28", "end": "2026-10-03"},
        {"kind": "ovulation", "title": "Ovulation (estimated)", "start": "2026-10-03", "end": "2026-10-03"},
        {"kind": "period", "title": "Predicted period", "start": "2026-10-17", "end": "2026-10-20"},
    ],
}


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations: None) -> Generator[None]:
    yield


@pytest.fixture
def feed() -> dict[str, Any]:
    return deepcopy(FEED)


@pytest.fixture
def entry() -> MockConfigEntry:
    return MockConfigEntry(
        domain="bloomery", title="Bloomery (Mia)", data={"url": URL}, unique_id="bloomery.local:8420_1", version=1
    )


@pytest.fixture
async def setup(
    hass: HomeAssistant, entry: MockConfigEntry, aioclient_mock: AiohttpClientMocker, feed: dict[str, Any]
) -> MockConfigEntry:
    aioclient_mock.get(URL, json=feed)
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry
