"""Daily notifications via ntfy / Gotify / Home Assistant / Discord / any JSON webhook.
Works over plain HTTP LAN installs (Web Push would need HTTPS). Settings live in the Setting table
under key "notify:<user_id>" as JSON, so no schema migration is needed."""

from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime
from urllib.parse import urlsplit
from zoneinfo import ZoneInfo

import httpx
from sqlmodel import Session, select

from . import contraception, push
from .db import get_engine
from .deps import bc_config, build_engine
from .feed import feed
from .models import DayLog, Setting, User

log = logging.getLogger("bloomery.notify")
KINDS = ("milestone", "forecast", "recap", "tip", "pill")
DEFAULTS = {"url": "", "time": "08:00", "tz": "UTC", "kinds": ["milestone", "forecast", "recap"], "last": ""}


def key(uid: int) -> str:
    return f"notify:{uid}"


def load(db: Session, uid: int) -> dict:
    row = db.get(Setting, key(uid))
    return {**DEFAULTS, **(json.loads(row.value) if row else {})}


def store(db: Session, uid: int, cfg: dict) -> None:
    db.merge(Setting(key=key(uid), value=json.dumps(cfg)))
    db.commit()


async def send(url: str, title: str, message: str) -> None:
    """Pick the payload shape from the URL. Raises httpx errors on failure."""
    u = urlsplit(url)
    async with httpx.AsyncClient(timeout=15) as c:
        if "ntfy" in u.netloc:  # JSON publish keeps emoji/unicode safe (headers can't carry them)
            r = await c.post(
                f"{u.scheme}://{u.netloc}",
                json={"topic": u.path.strip("/"), "title": title, "message": message, "tags": ["cherry_blossom"]},
            )
        elif "discord" in u.netloc:
            r = await c.post(url, json={"content": f"**{title}**\n{message}"})
        else:  # Gotify (…/message?token=…), Home Assistant webhook, generic
            r = await c.post(url, json={"title": title, "message": message, "priority": 5})
        r.raise_for_status()


async def deliver(db: Session, uid: int, url: str, title: str, message: str) -> int:
    """Send to the configured URL (ntfy/Gotify/HA/Discord) and to every push-enabled device. Returns deliveries."""
    n = 0
    if url:
        try:
            await send(url, title, message)
            n += 1
        except Exception as e:
            log.warning("notification to user %s via URL failed: %s", uid, e)
    try:
        n += await push.send(db, uid, title, message)
    except Exception as e:
        log.warning("push to user %s failed: %s", uid, e)
    return n


def compose(db: Session, user: User, today, kinds: list[str]) -> tuple[str, str] | None:
    logs = db.exec(select(DayLog).where(DayLog.user_id == user.id, DayLog.day <= today)).all()
    cards = [c for c in feed(build_engine(db, user, today), logs, today, user.goal) if c["kind"] in kinds]
    if "pill" in kinds:  # birth control reminders
        bc = contraception.status(bc_config(db, user.id), today)
        if bc and bc["action"]:
            cards.insert(0, bc)
        elif not bc_config(db, user.id):  # no method set up: the classic daily pill reminder
            cards.insert(0, {"emoji": "💊", "title": "Pill reminder", "text": "Time to take your pill."})
    if not cards:
        return None
    title = f"{cards[0]['emoji']} {cards[0]['title']}" + (f" (+{len(cards) - 1} more)" if len(cards) > 1 else "")
    return title, "\n\n".join(f"{c['emoji']} {c['title']}: {c['text']}" for c in cards)


async def tick(now_utc: datetime | None = None) -> int:
    """Send today's notification to every user whose local time has passed their chosen time. Returns sends."""
    now_utc = now_utc or datetime.now(ZoneInfo("UTC"))
    sent = 0
    with Session(get_engine()) as db:
        for row in db.exec(select(Setting).where(Setting.key.startswith("notify:"))).all():
            cfg = {**DEFAULTS, **json.loads(row.value)}
            uid = int(row.key.split(":")[1])
            if not cfg["url"] and not push.subscriptions(db, uid):
                continue
            try:
                local = now_utc.astimezone(ZoneInfo(cfg["tz"]))
            except Exception:
                local = now_utc
            today = local.date()
            if cfg["last"] == today.isoformat() or local.strftime("%H:%M") < cfg["time"]:
                continue
            user = db.get(User, uid)
            cfg["last"] = today.isoformat()  # mark first: a failing endpoint must not retry every minute
            store(db, uid, cfg)
            msg = user and compose(db, user, today, cfg["kinds"])
            if msg:
                sent += await deliver(db, uid, cfg["url"], *msg)
    return sent


async def scheduler() -> None:
    while True:
        try:
            await tick()
        except Exception:
            log.exception("notification tick failed")
        await asyncio.sleep(60)
