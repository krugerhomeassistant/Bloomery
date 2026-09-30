import asyncio
import json

import httpx
import pytest

from app import ai
from app.config import get_settings


@pytest.fixture
def mock_http(monkeypatch):
    seen = {}

    def handler(req: httpx.Request):
        seen["url"], seen["body"], seen["headers"] = str(req.url), json.loads(req.content), req.headers
        if "messages" in req.url.path and "chat" not in req.url.path:
            return httpx.Response(200, json={"content": [{"type": "text", "text": "hi from claude"}]})
        return httpx.Response(200, json={"choices": [{"message": {"content": "<think>x</think>hi from llm"}}]})

    real = httpx.AsyncClient
    monkeypatch.setattr(httpx, "AsyncClient", lambda **kw: real(transport=httpx.MockTransport(handler), **kw))
    return seen


def test_recap_endpoint(monkeypatch, mock_http):
    from fastapi.testclient import TestClient
    from app.main import app
    from app import ai as ai_mod
    with TestClient(app) as c:
        c.post("/api/auth/login", json={"username": "ana", "password": "supersecret"})
        if c.get("/api/auth/me").status_code != 200:
            c.post("/api/auth/register", json={"username": "ana", "password": "supersecret"})
        for d in ("2025-08-01", "2025-08-29"):
            c.post(f"/api/period/start?today={d}", json={"day": d})
        c.put("/api/ai/config", json={"provider": "none"})
        r = c.get("/api/ai/recap?start=2025-08-01&today=2025-09-05").json()
        assert r["source"] == "rules" and r["length"] == 28 and "28 days" in r["content"]
        assert c.get("/api/ai/recap?start=2025-08-02&today=2025-09-05").status_code == 404
        monkeypatch.setattr(ai_mod, "config", lambda override=None: {"provider": "ollama", "base_url": "http://ollama:11434/v1", "model": "m", "api_key": ""})
        r = c.get("/api/ai/recap?start=2025-08-01&today=2025-09-05").json()
        assert r["source"] == "ai" and r["content"] == "hi from llm"
        assert "CYCLE DATA" in mock_http["body"]["messages"][0]["content"]
        assert c.get("/api/ai/recap?start=2025-08-01&today=2025-09-05").json().get("cached")  # completed → cached
