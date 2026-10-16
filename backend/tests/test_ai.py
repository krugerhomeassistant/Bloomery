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


@pytest.mark.parametrize(
    "provider,expect_url,expect",
    [
        ("ollama", "http://ollama:11434/v1/chat/completions", "hi from llm"),
        ("anthropic", "https://api.anthropic.com/v1/messages", "hi from claude"),
        ("openai", "https://api.openai.com/v1/chat/completions", "hi from llm"),
    ],
)
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


def test_list_models(monkeypatch):
    def handler(req: httpx.Request):
        if "anthropic" in req.url.host:
            assert req.headers["x-api-key"] == "k" and req.url.path == "/v1/models"
            return httpx.Response(200, json={"data": [{"id": "claude-b"}, {"id": "claude-a"}]})
        assert req.url.path == "/v1/models" and req.headers["authorization"] == "Bearer k"
        return httpx.Response(
            200,
            json={
                "data": [
                    {"id": i}
                    for i in ("gpt-5", "text-embedding-3", "gpt-image-1", "whisper-1", "o3-mini", "gpt-5-mini")
                ]
            },
        )

    real = httpx.AsyncClient
    monkeypatch.setattr(httpx, "AsyncClient", lambda **kw: real(transport=httpx.MockTransport(handler), **kw))
    cfg = lambda p: ai.config({"provider": p, "api_key": "k"})
    assert asyncio.run(ai.list_models(cfg("anthropic"))) == ["claude-b", "claude-a"]  # API order kept: newest first
    assert asyncio.run(ai.list_models(cfg("openai"))) == ["gpt-5", "gpt-5-mini", "o3-mini"]
    with pytest.raises(ai.AIError):
        asyncio.run(ai.list_models(ai.config({"provider": "custom"})))  # no base URL
