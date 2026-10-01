"""Minimal async client for a Bloomery server's read-only Home Assistant feed."""

from __future__ import annotations

import re
from typing import Any

from aiohttp import ClientError, ClientSession, ClientTimeout

FEED_RE = re.compile(r"^(https?://[^?#]+?)/api/ha/([A-Za-z0-9_-]{8,})/?(?:[?#].*)?$")


class BloomeryError(Exception):
    """Base error."""


class BloomeryConnectionError(BloomeryError):
    """Server unreachable or returned an unexpected response."""


class BloomeryAuthError(BloomeryError):
    """The feed token was revoked or regenerated."""


def normalize_url(url: str) -> str | None:
    """Return the feed URL without query/fragment, or None if it isn't a Bloomery feed URL."""
    m = FEED_RE.match(url.strip())
    return f"{m.group(1)}/api/ha/{m.group(2)}" if m else None


class BloomeryClient:
    """Reads `GET <server>/api/ha/<token>` using Home Assistant's shared aiohttp session."""

    def __init__(self, session: ClientSession, url: str, time_zone: str) -> None:
        self._session = session
        self.url = url
        self._tz = time_zone

    @property
    def base_url(self) -> str:
        return self.url.split("/api/ha/")[0]

    async def async_get_state(self) -> dict[str, Any]:
        try:
            async with self._session.get(self.url, params={"tz": self._tz}, timeout=ClientTimeout(total=15)) as r:
                if r.status == 404:
                    raise BloomeryAuthError
                r.raise_for_status()
                data: dict[str, Any] = await r.json()
        except (ClientError, TimeoutError, ValueError) as err:
            raise BloomeryConnectionError(str(err) or type(err).__name__) from err
        return data
