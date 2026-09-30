"""LLM provider abstraction (httpx, no SDKs) + context building.

Providers: anthropic (/v1/messages) · openai / openrouter / ollama / custom (OpenAI /chat/completions).
Config: env BLOOMERY_AI_* < in-app settings (Setting table, admin-only) < per-call override (connection test).
Only aggregated stats + recent logs are sent; nothing leaves the box when provider=none or ollama.
"""
from __future__ import annotations

import json
import re
from datetime import date, timedelta

import httpx
from sqlalchemy.exc import OperationalError
from sqlmodel import Session, select

from .catalog import LABELS
from .config import get_settings
from .cycles import Engine
from .feed import forecasts
from .db import get_engine
from .models import Setting

SYSTEM = """You are Bloomery, a warm, knowledgeable menstrual-health companion inside a private, self-hosted period tracker.
Style: friendly, concise, plain language, second person. Use short paragraphs or brief bullet lists. No markdown headings.
Ground every personal statement in the user's data provided below; say so when data is thin. Be clear predictions are estimates.
Safety: you are not a doctor and don't diagnose. Recommend a healthcare professional for severe pain, very heavy bleeding,
missed periods with possible pregnancy, cycles persistently <21 or >35 days, or anything worrying. Never present
calendar/fertility predictions as reliable contraception. For emergencies, advise contacting emergency services.
If life_stage is "pregnancy", talk about pregnancy week, baby development and trimester care instead of cycle phases, and
urge prompt care for bleeding, severe pain, severe headache, vision changes or reduced baby movement. If "perimenopause",
expect irregular cycles and symptoms like hot flashes, night sweats and sleep changes; bleeding after 12 months without a period needs a doctor."""


class AIError(RuntimeError):
    pass


# provider -> (default base_url, default model). openrouter/ollama/custom speak the OpenAI chat schema.
PROVIDERS: dict[str, tuple[str, str]] = {
    "anthropic": ("https://api.anthropic.com", "claude-haiku-4-5-20251001"),
    "openai": ("https://api.openai.com/v1", "gpt-5-mini"),
    "openrouter": ("https://openrouter.ai/api/v1", "openrouter/auto"),
    "ollama": ("http://ollama:11434/v1", "llama3.2:3b"),
    "custom": ("", ""),
}
KEYS = ("provider", "base_url", "model", "api_key")


def stored() -> dict[str, str]:
    """In-app settings (DB), empty dict if the table isn't there yet."""
    try:
        with Session(get_engine()) as db:
            return {r.key.removeprefix("ai_"): r.value for r in db.exec(select(Setting)).all() if r.key.startswith("ai_")}
    except OperationalError:
        return {}


def config(override: dict | None = None) -> dict[str, str]:
    """Effective config: env < DB < override. Blank base_url/model fall back to provider defaults."""
    s = get_settings()
    cfg = {"provider": s.ai_provider, "base_url": s.ai_base_url, "model": s.ai_model, "api_key": s.ai_api_key}
    for src in (stored(), override or {}):
        if src.get("provider") and src["provider"] != cfg["provider"]:  # never reuse another provider's url/model/key
            cfg.update(provider=src["provider"], base_url="", model="", api_key="")
        cfg.update({k: v for k, v in src.items() if k in KEYS and k != "provider" and v is not None})
    cfg["provider"] = cfg["provider"].lower()
    base, model = PROVIDERS.get(cfg["provider"], ("", ""))
    cfg["base_url"] = (cfg["base_url"] or base).rstrip("/")
    cfg["model"] = cfg["model"] or model
    return cfg


def save(values: dict) -> None:
    if values.get("provider"):  # blank url/model = provider defaults
        values = {**values, "base_url": values.get("base_url") or "", "model": values.get("model") or ""}
        if values["provider"] != config()["provider"] and values.get("api_key") is None:
            values["api_key"] = ""  # don't carry a key over to a different provider
    with Session(get_engine()) as db:
        for k in KEYS:
            if values.get(k) is not None:
                db.merge(Setting(key=f"ai_{k}", value=values[k]))
        db.commit()


def enabled(cfg: dict | None = None) -> bool:
    return (cfg or config())["provider"] in PROVIDERS


def info() -> dict:
    cfg = config()
    on = enabled(cfg)
    return {"enabled": on, "provider": cfg["provider"], "model": cfg["model"] if on else None,
            "local": cfg["provider"] == "ollama"}


_THINK = re.compile(r"<think>.*?</think>", re.S)


def _request(cfg: dict, system: str, messages: list[dict], max_tokens: int, stream: bool) -> tuple[str, dict, dict]:
    """(url, headers, json body) for the configured provider."""
    provider, base, model, key = cfg["provider"], cfg["base_url"], cfg["model"], cfg["api_key"]
    if provider not in PROVIDERS:
        raise AIError("AI is turned off. Enable it in Profile → AI assistant.")
    if not base or not model:
        raise AIError("Base URL and model are required for this provider.")
    if provider == "anthropic":
        return (f"{base}/v1/messages",
                {"x-api-key": key, "anthropic-version": "2023-06-01", "content-type": "application/json"},
                {"model": model, "max_tokens": max_tokens, "system": system, "messages": messages, "stream": stream})
    body = {"model": model, "messages": [{"role": "system", "content": system}, *messages], "stream": stream}
    if provider == "openai":  # GPT-5 family: no temperature; reasoning tokens count toward the cap
        body["max_completion_tokens"] = max_tokens * 4
    else:
        body.update(max_tokens=max_tokens, temperature=0.6)
    return f"{base}/chat/completions", ({"Authorization": f"Bearer {key}"} if key else {}), body


def _status_error(r: httpx.Response) -> AIError:
    try:  # Anthropic & OpenAI both use {"error": {"message": ...}}
        detail = r.json()["error"]["message"]
    except Exception:
        detail = r.text[:300]
    return AIError(f"AI provider returned {r.status_code}: {detail}")


async def complete(system: str, messages: list[dict], max_tokens: int = 700, cfg: dict | None = None) -> str:
    cfg = cfg or config()
    url, headers, body = _request(cfg, system, messages, max_tokens, stream=False)
    try:
        async with httpx.AsyncClient(timeout=get_settings().ai_timeout) as c:
            r = await c.post(url, json=body, headers=headers)
    except httpx.HTTPError as e:
        raise AIError(f"Could not reach AI provider at {cfg['base_url']}: {e.__class__.__name__}") from e
    if r.status_code >= 400:
        raise _status_error(r)
    j = r.json()
    if cfg["provider"] == "anthropic":
        text = "".join(b.get("text", "") for b in j.get("content", []) if b.get("type") == "text")
    else:
        text = j["choices"][0]["message"]["content"] or ""
    return _THINK.sub("", text).strip()


async def stream(system: str, messages: list[dict], max_tokens: int = 700, cfg: dict | None = None):
    """Yields text chunks as the provider produces them (SSE from Anthropic or OpenAI-compatible APIs)."""
    cfg = cfg or config()
    url, headers, body = _request(cfg, system, messages, max_tokens, stream=True)
    anthropic = cfg["provider"] == "anthropic"
    try:
        async with httpx.AsyncClient(timeout=get_settings().ai_timeout) as c, c.stream("POST", url, json=body, headers=headers) as r:
            if r.status_code >= 400:
                await r.aread()
                raise _status_error(r)
            async for line in r.aiter_lines():
                if not line.startswith("data:"):
                    continue
                data = line[5:].strip()
                if data == "[DONE]":
                    break
                try:
                    j = json.loads(data)
                except json.JSONDecodeError:
                    continue
                if anthropic:
                    if j.get("type") == "error":
                        raise AIError(f"AI provider error: {j.get('error', {}).get('message', 'unknown')}")
                    if j.get("type") == "content_block_delta" and j["delta"].get("type") == "text_delta":
                        yield j["delta"]["text"]
                elif (ch := j.get("choices")) and (t := (ch[0].get("delta") or {}).get("content")):
                    yield t
    except httpx.HTTPError as e:
        raise AIError(f"Could not reach AI provider at {cfg['base_url']}: {e.__class__.__name__}") from e


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
        "life_stage": engine.profile.mode,
        "pregnancy": ov["pregnancy"],
        "age": (t.year - user.birth_year) if user.birth_year else None,
        "status": ov["status"],
        "next_period": ov["next_period"],
        "predicted_cycle_length": ov["predicted_cycle_length"],
        "predicted_period_length": ov["predicted_period_length"],
        "current_cycle": ov["current_cycle"],
        "stats": {k: v for k, v in engine.stats().items() if k != "history"},
        "recent_cycles": engine.stats()["history"][:6],
        "flags": [f["title"] for f in engine.flags()],
        "heads_up_today": [f["title"] for f in forecasts(engine, logs, t)],  # symptoms likely today from history
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


def recap_context(engine: Engine, logs: list, seg) -> str:
    """Everything about one cycle, compact, for the recap prompt."""
    days = []
    for l in sorted(logs, key=lambda x: x.day):
        if seg.start <= l.day <= seg.end:
            row = {"cd": (l.day - seg.start).days + 1, "ph": engine.day_info(l.day)["phase"]}
            if l.flow:
                row["flow"] = l.flow
            tags = [LABELS.get(f"{c}:{v}", v) for c, vs in (l.tags or {}).items() for v in vs]
            if tags:
                row["tags"] = tags
            if l.temperature:
                row["bbt"] = l.temperature
            if l.notes:
                row["note"] = l.notes[:200]
            days.append(row)
    st = engine.stats()
    done = seg.end < engine.today
    return json.dumps({
        "cycle": {"start": seg.start.isoformat(), "length_days": seg.length if done else None,
                  "days_so_far": None if done else (engine.today - seg.start).days + 1,
                  "period_days": (seg.period_end - seg.start).days + 1, "ovulation": seg.ovulation.isoformat(),
                  "ovulation_confirmed_by_bbt": seg.ovulation_confirmed},
        "averages": {"cycle": st["avg_cycle_length"], "period": st["avg_period_length"], "regularity": st["regularity"]},
        "recent_cycle_lengths": [h["length"] for h in st["history"] if h["length"]][:6],
        "logs": days,
    }, separators=(",", ":"))


RECAP_PROMPT = ("Write a recap of this cycle for me. Use 3-5 short bullet points (start each with •): how its length compares "
                "to my average, my period, which symptoms/moods showed up in which phase, and anything notable (e.g. a "
                "temperature shift or unusual pattern). Only mention things in the data. Then one final line starting "
                "'For next cycle:' with one practical, specific tip. Max 130 words. No greeting.")


def daily_prompt(day: date) -> str:
    return (f"Write today's personal insight for {day.isoformat()} in 2-4 short sentences (max 90 words). "
            "Explain what's likely happening in my body in this phase (or pregnancy week / life stage), connect it to anything notable in my recent logs "
            "(patterns, symptoms, moods, temperature, and heads_up_today forecasts), and give one practical, specific tip. No greeting, no disclaimer "
            "unless a health flag warrants it.")
