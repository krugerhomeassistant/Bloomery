import asyncio
import json
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

import httpx
from fastapi.testclient import TestClient

from app import notify
from app.main import app


def test_notifications_schedule_and_payloads(monkeypatch):
    sent = []

    def handler(req: httpx.Request):
        sent.append((str(req.url), json.loads(req.content)))
        return httpx.Response(200)

    real = httpx.AsyncClient
    monkeypatch.setattr(httpx, "AsyncClient", lambda **kw: real(transport=httpx.MockTransport(handler), **kw))

    with TestClient(app) as c:
        c.post("/api/auth/login", json={"username": "ana", "password": "supersecret"})  # user from test_api
        if c.get("/api/auth/me").status_code != 200:
            c.post("/api/auth/register", json={"username": "ana", "password": "supersecret"})
        today = date(2026, 3, 1)
        c.post(f"/api/period/start?today={today}", json={"day": str(today)})
        assert c.put("/api/notifications", json={"url": "ftp://x"}).status_code == 422
        assert c.put("/api/notifications", json={"url": "https://x", "tz": "Mars/Base"}).status_code == 422
        r = c.put(
            "/api/notifications",
            json={
                "url": "https://ntfy.sh/bloom-test",
                "time": "08:00",
                "tz": "Africa/Johannesburg",
                "kinds": ["milestone", "pill"],
            },
        )
        assert r.status_code == 200 and "last" not in r.json()

        # ntfy gets JSON publish to the root with topic
        assert c.post(f"/api/notifications/test?today={today}", json=r.json()).json()["ok"]
        url, body = sent[-1]
        assert (
            url.rstrip("/") == "https://ntfy.sh"
            and body["topic"] == "bloom-test"
            and "Pill reminder" in body["message"]
        )
        assert "Your period started" in body["message"]

    # 07:59 local (05:59 UTC) → nothing; 08:00 → one send; same day again → nothing
    t = datetime(2026, 3, 1, 5, 59, tzinfo=ZoneInfo("UTC"))
    n = len(sent)
    assert asyncio.run(notify.tick(t)) == 0
    assert asyncio.run(notify.tick(t + timedelta(minutes=1))) == 1
    assert asyncio.run(notify.tick(t + timedelta(hours=3))) == 0
    assert len(sent) == n + 1


def test_payload_shapes(monkeypatch):
    sent = []
    real = httpx.AsyncClient
    monkeypatch.setattr(
        httpx,
        "AsyncClient",
        lambda **kw: real(
            transport=httpx.MockTransport(
                lambda r: sent.append((str(r.url), json.loads(r.content))) or httpx.Response(204)
            ),
            **kw,
        ),
    )
    asyncio.run(notify.send("https://discord.com/api/webhooks/1/x", "T", "M"))
    asyncio.run(notify.send("http://gotify.lan/message?token=abc", "T", "M"))
    assert sent[0][1] == {"content": "**T**\nM"}
    assert sent[1] == ("http://gotify.lan/message?token=abc", {"title": "T", "message": "M", "priority": 5})
