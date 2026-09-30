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


@pytest.mark.parametrize("provider,expect_url,expect", [
    ("ollama", "http://ollama:11434/v1/chat/completions", "hi from llm"),
    ("anthropic", "https://api.anthropic.com/v1/messages", "hi from claude"),
    ("openai", "https://api.openai.com/v1/chat/completions", "hi from llm"),
])
def test_providers(monkeypatch, mock_http, provider, expect_url, expect):
    s = get_settings()
    monkeypatch.setattr(s, "ai_provider", provider)
    monkeypatch.setattr(s, "ai_api_key", "k")
    out = asyncio.run(ai.complete("sys", [{"role": "user", "content": "q"}]))
    assert out == expect
    assert mock_http["url"] == expect_url
    if provider == "anthropic":
        assert mock_http["body"]["system"] == "sys" and mock_http["headers"]["x-api-key"] == "k"
    else:
        assert mock_http["body"]["messages"][0]["role"] == "system"
    if provider == "openai":  # GPT-5 family rejects max_tokens/temperature
        assert "max_completion_tokens" in mock_http["body"] and "temperature" not in mock_http["body"]

