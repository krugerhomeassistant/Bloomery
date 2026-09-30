"""LLM provider abstraction (httpx, no SDKs) + context building.

Providers: ollama / openai (any OpenAI-compatible /chat/completions) / anthropic (/v1/messages).
Only aggregated stats + recent logs are sent; nothing leaves the box when provider=none or ollama.
"""
from __future__ import annotations

import json
import re
from datetime import date, timedelta

import httpx

from .catalog import LABELS
from .config import get_settings
from .cycles import Engine

SYSTEM = """You are Bloomery, a warm, knowledgeable menstrual-health companion inside a private, self-hosted period tracker.
Style: friendly, concise, plain language, second person. Use short paragraphs or brief bullet lists. No markdown headings.
Ground every personal statement in the user's data provided below; say so when data is thin. Be clear predictions are estimates.
Safety: you are not a doctor and don't diagnose. Recommend a healthcare professional for severe pain, very heavy bleeding,
missed periods with possible pregnancy, cycles persistently <21 or >35 days, or anything worrying. Never present
calendar/fertility predictions as reliable contraception. For emergencies, advise contacting emergency services."""


class AIError(RuntimeError):
    pass


def enabled() -> bool:
    return get_settings().ai_provider.lower() in {"ollama", "openai", "anthropic"}


def info() -> dict:
    s = get_settings()
    base, model = s.ai_defaults
    return {"enabled": enabled(), "provider": s.ai_provider.lower(), "model": model if enabled() else None,
            "local": s.ai_provider.lower() == "ollama"}


_THINK = re.compile(r"<think>.*?</think>", re.S)


async def complete(system: str, messages: list[dict], max_tokens: int = 700) -> str:
    s = get_settings()
    provider = s.ai_provider.lower()
    base, model = s.ai_defaults
    try:
        async with httpx.AsyncClient(timeout=s.ai_timeout) as c:
            if provider == "anthropic":
                r = await c.post(f"{base}/v1/messages", headers={
                    "x-api-key": s.ai_api_key, "anthropic-version": "2023-06-01", "content-type": "application/json"},
                    json={"model": model, "max_tokens": max_tokens, "system": system, "messages": messages})
                r.raise_for_status()
                text = "".join(b.get("text", "") for b in r.json().get("content", []) if b.get("type") == "text")
            elif provider in {"openai", "ollama"}:
                headers = {"Authorization": f"Bearer {s.ai_api_key}"} if s.ai_api_key else {}
                r = await c.post(f"{base}/chat/completions", headers=headers, json={
                    "model": model, "max_tokens": max_tokens, "temperature": 0.6,
                    "messages": [{"role": "system", "content": system}, *messages]})
                r.raise_for_status()
                text = r.json()["choices"][0]["message"]["content"] or ""
            else:
                raise AIError("AI is disabled. Set BLOOMERY_AI_PROVIDER to enable it.")
    except httpx.HTTPStatusError as e:
        raise AIError(f"AI provider returned {e.response.status_code}: {e.response.text[:300]}") from e
    except httpx.HTTPError as e:
        raise AIError(f"Could not reach AI provider at {base}: {e.__class__.__name__}") from e
    return _THINK.sub("", text).strip()


def build_context(engine: Engine, logs: list, user) -> str:
    """Compact, token-dense JSON summary of the user's cycle for the LLM."""
    t = engine.today
    recent = []
    for l in sorted(logs, key=lambda x: x.day):
        if l.day < t - timedelta(days=60) or l.day > t:
            continue
        info = engine.day_info(l.day)
        row = {"d": l.day.isoformat(), "cd": info["cycle_day"], "ph": info["phase"]}
        if l.flow:
            row["flow"] = l.flow
        tags = [LABELS.get(f"{c}:{v}", v) for c, vs in (l.tags or {}).items() for v in vs]
        if tags:
            row["tags"] = tags
        for k in ("temperature", "weight", "sleep_hours", "water_ml"):
            if getattr(l, k):
                row[k] = getattr(l, k)
        if l.notes:
            row["note"] = l.notes[:200]
        recent.append(row)
    ov = engine.overview()
    ctx = {
        "today": t.isoformat(),
        "goal": user.goal,
        "age": (t.year - user.birth_year) if user.birth_year else None,
        "status": ov["status"],
        "next_period": ov["next_period"],
        "predicted_cycle_length": ov["predicted_cycle_length"],
        "predicted_period_length": ov["predicted_period_length"],
        "current_cycle": ov["current_cycle"],
        "stats": {k: v for k, v in engine.stats().items() if k != "history"},
        "recent_cycles": engine.stats()["history"][:6],
        "flags": [f["title"] for f in engine.flags()],
        "logs_last_60_days": recent,
    }
    return json.dumps(ctx, separators=(",", ":"), default=str)


PHASE_TIPS = {
    "menstrual": "Your body is shedding the uterine lining. Warmth, gentle movement and iron-rich foods can help with cramps and fatigue.",
    "follicular": "Estrogen is rising, which often brings more energy and a brighter mood — a good time for new projects and harder workouts.",
    "fertile": "You're in your fertile window. Cervical fluid often becomes clearer and stretchier around now.",
    "ovulation": "Ovulation is estimated for today. Some people notice mild one-sided pain or a small temperature rise afterwards.",
    "luteal": "Progesterone is higher now. It's common to feel more tired, bloated or crave comfort food before your period.",
}


def fallback_insight(engine: Engine) -> str:
    st = engine.status()
    phase = st.get("phase")
    if st.get("state") == "empty":
        return "Log your last period to unlock predictions and personalised insights."
    parts = [PHASE_TIPS.get(phase or "", "")]
    stats = engine.stats()
    if stats["avg_cycle_length"]:
        parts.append(f"Your average cycle is {stats['avg_cycle_length']} days across {stats['cycles_tracked']} tracked cycles.")
    return " ".join(p for p in parts if p)


def daily_prompt(day: date) -> str:
    return (f"Write today's personal insight for {day.isoformat()} in 2-4 short sentences (max 90 words). "
            "Explain what's likely happening in my body in this phase, connect it to anything notable in my recent logs "
            "(patterns, symptoms, moods, temperature), and give one practical, specific tip. No greeting, no disclaimer "
            "unless a health flag warrants it.")
