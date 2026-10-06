"""Quick logging with an API key, for Home Assistant actions, Siri Shortcuts, NFC tags and scripts.

The key (token kind "api", Profile → Shortcuts & automations) can only use these endpoints:
`Authorization: Bearer <key>`. Days default to today in `tz` (IANA zone) or the server's date.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Annotated
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel, Field
from sqlmodel import Session

from ..catalog import CATALOG, LABELS, catalog_json
from ..db import get_session
from ..models import DayLog, Setting, User, now
from .tracking import PeriodStart, _get_log, period_start

router = APIRouter(prefix="/api/quick", tags=["quick log"])


def key_user(db: Annotated[Session, Depends(get_session)], authorization: Annotated[str, Header()] = "") -> User:
    token = authorization.removeprefix("Bearer ").strip()
    row = db.get(Setting, f"api:{token}") if token and token != authorization else None
    user = db.get(User, int(row.value)) if row else None
    if not user:
        raise HTTPException(401, "Invalid or missing API key", headers={"WWW-Authenticate": "Bearer"})
    return user


KeyUser = Annotated[User, Depends(key_user)]
DB = Annotated[Session, Depends(get_session)]


def _day(day: date | None, tz: str | None) -> date:
    if day:
        return day
    try:
        return datetime.now(ZoneInfo(tz)).date() if tz else date.today()
    except Exception as e:
        raise HTTPException(422, f"Unknown time zone {tz!r}") from e


# lookup by "cat:id", id, or label (case-insensitive), in catalog order; "none" is too ambiguous to resolve
_BY_NAME: dict[str, tuple[str, str]] = {}
for _c in reversed(CATALOG):
    for _i, _label, _ in _c["items"]:
        if _i != "none":
            _BY_NAME[_i.lower()] = _BY_NAME[_label.lower()] = (_c["id"], _i)


def resolve(name: str) -> tuple[str, str] | None:
    n = name.strip().lower()
    if ":" in n and f"{n.split(':')[0]}:{n.split(':')[1]}" in LABELS:
        c, i = n.split(":", 1)
        return c, i
    return _BY_NAME.get(n.replace(" ", "_")) or _BY_NAME.get(n)


class QuickLog(BaseModel):
    day: date | None = None
    tz: str | None = Field(None, max_length=64)
    tags: list[str] = Field(default_factory=list, max_length=30, description='Ids, labels or "category:id", e.g. ["Cramps", "mood:sad"]')
    flow: str | None = Field(None, pattern="^(spotting|light|medium|heavy)$")
    temperature: float | None = Field(None, ge=30, le=110)
    temperature_unit: str = Field("C", pattern="^[CF]$")
    note: str | None = Field(None, max_length=1000)


@router.get("/catalog")
def quick_catalog(user: KeyUser):
    """Everything you can log, with ids and labels (for Shortcut menus)."""
    return catalog_json()


@router.post("/period-start")
def quick_period_start(user: KeyUser, db: DB, body: QuickLog | None = None):
    body = body or QuickLog()
    day = _day(body.day, body.tz)
    r = period_start(PeriodStart(day=day), user, db, day)
    return {"ok": True, "date": day.isoformat(), "days": r["days"]}


@router.post("/log")
def quick_log(body: QuickLog, user: KeyUser, db: DB):
    """Add to a day's log without removing anything already logged."""
    day = _day(body.day, body.tz)
    resolved = [(t, resolve(t)) for t in body.tags]
    if unknown := [t for t, r in resolved if not r]:
        raise HTTPException(422, f"Unknown: {', '.join(unknown)}. See GET /api/quick/catalog")
    if not (resolved or body.flow or body.temperature is not None or body.note):
        raise HTTPException(422, "Nothing to log")
    log = _get_log(db, user, day) or DayLog(user_id=user.id, day=day)
    tags = {c: list(v) for c, v in (log.tags or {}).items()}
    pairs = [r for _, r in resolved if r]
    for cat, item in pairs:
        if item not in tags.setdefault(cat, []):
            tags[cat].append(item)
    log.tags = tags
    if body.flow:
        log.flow = body.flow
    if body.temperature is not None:
        t = body.temperature
        log.temperature = round((t - 32) * 5 / 9, 2) if body.temperature_unit == "F" else t
        if not 34 <= log.temperature <= 43:
            raise HTTPException(422, "That temperature doesn't look like a body temperature")
    if body.note:
        log.notes = f"{log.notes}\n{body.note}".strip() if log.notes else body.note
    log.updated_at = now()
    db.add(log)
    db.commit()
    return {"ok": True, "date": day.isoformat(), "logged": [LABELS[f"{c}:{i}"] for c, i in pairs]}
