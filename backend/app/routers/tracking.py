import json
from datetime import date, timedelta
from typing import Literal

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field, field_validator
from sqlmodel import delete, select

from .. import feed as feed_mod
from ..catalog import LABELS, VALID, catalog_json
from ..cycles import symptom_heatmap, symptom_patterns
from ..deps import SessionDep, TodayDep, UserDep, build_engine
from ..models import BLEEDING, ChatMessage, DayLog, InsightCache, Setting, User, now
from .auth import public_user

router = APIRouter(prefix="/api", tags=["tracking"])
D = timedelta


@router.get("/catalog")
def catalog():
    return catalog_json()


# ---------------------------------------------------------------- profile
class ProfileIn(BaseModel):
    display_name: str | None = None
    cycle_length: int | None = Field(None, ge=15, le=90)
    period_length: int | None = Field(None, ge=1, le=15)
    luteal_length: int | None = Field(None, ge=8, le=20)
    goal: Literal["track", "conceive", "avoid"] | None = None
    birth_year: int | None = Field(None, ge=1900, le=2100)
    temp_unit: Literal["C", "F"] | None = None
    weight_unit: Literal["kg", "lb"] | None = None
    onboarded: bool | None = None


@router.put("/profile")
def update_profile(body: ProfileIn, user: UserDep, db: SessionDep):
    for k, v in body.model_dump(exclude_none=True).items():
        setattr(user, k, v)
    db.add(user)
    db.commit()
    db.refresh(user)
    return public_user(user)


class LifeStageIn(BaseModel):
    mode: Literal["cycle", "pregnancy", "perimenopause"]
    lmp: date | None = None


@router.put("/life-stage")
def set_life_stage(body: LifeStageIn, user: UserDep, db: SessionDep):
    lmp = body.lmp.isoformat() if body.mode == "pregnancy" and body.lmp else None
    db.merge(Setting(key=f"mode:{user.id}", value=json.dumps({"mode": body.mode, "lmp": lmp})))
    db.exec(
        delete(InsightCache).where(InsightCache.user_id == user.id)
    )  # daily AI insight was written for the old stage
    db.commit()
    return public_user(user)


# ---------------------------------------------------------------- day logs
class LogIn(BaseModel):
    flow: Literal["spotting", "light", "medium", "heavy"] | None = None
    tags: dict[str, list[str]] = {}
    temperature: float | None = Field(None, ge=34, le=43)
    weight: float | None = Field(None, gt=0, lt=500)
    water_ml: int | None = Field(None, ge=0, le=20000)
    sleep_hours: float | None = Field(None, ge=0, le=24)
    notes: str = Field("", max_length=5000)

    @field_validator("tags")
    @classmethod
    def _valid_tags(cls, v: dict[str, list[str]]):
        out = {}
        for cat, vals in v.items():
            if cat not in VALID:
                raise ValueError(f"unknown category {cat}")
            bad = set(vals) - VALID[cat]
            if bad:
                raise ValueError(f"unknown {cat} values {sorted(bad)}")
            if vals:
                out[cat] = sorted(set(vals))
        return out


def _get_log(db, user: User, d: date) -> DayLog | None:
    return db.exec(select(DayLog).where(DayLog.user_id == user.id, DayLog.day == d)).first()


def _is_empty(l: DayLog) -> bool:
    return not (l.flow or l.tags or l.temperature or l.weight or l.water_ml or l.sleep_hours or l.notes)


@router.get("/logs")
def list_logs(user: UserDep, db: SessionDep, start: date, end: date):
    rows = db.exec(
        select(DayLog).where(DayLog.user_id == user.id, DayLog.day >= start, DayLog.day <= end).order_by(DayLog.day)
    ).all()
    return [r.model_dump(exclude={"user_id", "id"}) for r in rows]


@router.get("/logs/{day}")
def get_log(day: date, user: UserDep, db: SessionDep):
    l = _get_log(db, user, day)
    return l.model_dump(exclude={"user_id", "id"}) if l else {"day": day, "flow": None, "tags": {}, "notes": ""}


@router.put("/logs/{day}")
def put_log(day: date, body: LogIn, user: UserDep, db: SessionDep):
    l = _get_log(db, user, day) or DayLog(user_id=user.id, day=day)
    before = {f"{c}:{v}" for c, vs in (l.tags or {}).items() for v in vs}
    for k, v in body.model_dump().items():
        setattr(l, k, v)
    l.updated_at = now()
    if _is_empty(l):
        if l.id:
            db.delete(l)
        db.commit()
        return {"day": day, "deleted": True}
    db.add(l)
    db.commit()
    db.refresh(l)
    out = l.model_dump(exclude={"user_id", "id"})
    if l.tags:
        eng = build_engine(db, user, day)
        logs = db.exec(select(DayLog).where(DayLog.user_id == user.id)).all()
        pats = symptom_patterns(eng, [(x.day, x.tags) for x in logs], LABELS)["patterns"]
        added: dict[str, list[str]] = {}  # comment only on what was just added
        for c, vs in l.tags.items():
            added[c] = [v for v in vs if f"{c}:{v}" not in before]
        out["note"] = feed_mod.log_note(eng, pats, day, added)
        if out["note"]:  # keep the latest note so Today can show it again as a card
            db.merge(Setting(key=f"lognote:{user.id}", value=json.dumps({"day": day.isoformat(), "text": out["note"]})))
            db.commit()
    return out


# ---------------------------------------------------------------- period editing
class PeriodEdit(BaseModel):
    add: list[date] = []
    remove: list[date] = []


def _set_flow(db, user: User, d: date, flow: str | None):
    l = _get_log(db, user, d)
    if flow is None:
        if l and l.flow:
            l.flow = None
            if _is_empty(l):
                db.delete(l)
            else:
                db.add(l)
        return
    if l is None:
        l = DayLog(user_id=user.id, day=d)
    if l.flow not in BLEEDING:
        l.flow = flow
    db.add(l)


@router.put("/period")
def edit_period(body: PeriodEdit, user: UserDep, db: SessionDep):
    """Calendar edit mode: toggle bleeding days."""
    for d in body.add:
        _set_flow(db, user, d, "medium")
    for d in body.remove:
        _set_flow(db, user, d, None)
    db.commit()
    return {"ok": True}


class PeriodStart(BaseModel):
    day: date


@router.post("/period/start")
def period_start(body: PeriodStart, user: UserDep, db: SessionDep, today: TodayDep):
    """Flo-style 'Log period': mark start + expected length (user can trim later)."""
    eng = build_engine(db, user, today)
    for i in range(eng.predicted_period):
        _set_flow(db, user, body.day + D(days=i), "medium")
    db.commit()
    return {"ok": True, "days": eng.predicted_period}


@router.post("/period/end")
def period_end(body: PeriodStart, user: UserDep, db: SessionDep):
    """Mark `day` as the last period day: clears bleeding in the following contiguous run."""
    d = body.day + D(days=1)
    while (l := _get_log(db, user, d)) and l.flow in BLEEDING:
        _set_flow(db, user, d, None)
        d += D(days=1)
    db.commit()
    return {"ok": True}


# ---------------------------------------------------------------- cycle views
@router.get("/cycle/overview")
def overview(user: UserDep, db: SessionDep, today: TodayDep):
    return build_engine(db, user, today).overview()


@router.get("/cycle/calendar")
def calendar(user: UserDep, db: SessionDep, today: TodayDep, start: date, end: date):
    if (end - start).days > 800:
        raise HTTPException(400, "Range too large")
    eng = build_engine(db, user, today)
    days = eng.calendar(start, end)
    logs = {
        l.day.isoformat(): l
        for l in db.exec(select(DayLog).where(DayLog.user_id == user.id, DayLog.day >= start, DayLog.day <= end)).all()
    }
    for d in days:
        l = logs.get(d["date"])
        d["flow"] = l.flow if l else None
        d["has_log"] = bool(l and (l.tags or l.notes or l.temperature or l.weight))
    return days


@router.get("/feed")
def daily_feed(user: UserDep, db: SessionDep, today: TodayDep):
    """Rule-based cards for Today: milestones, recap, symptom forecasts, phase tip."""
    logs = db.exec(select(DayLog).where(DayLog.user_id == user.id, DayLog.day <= today)).all()
    cards = feed_mod.feed(build_engine(db, user, today), logs, today, user.goal)
    note = db.get(Setting, f"lognote:{user.id}")
    if note and (n := json.loads(note.value))["day"] == today.isoformat():
        cards.insert(0, {"kind": "note", "emoji": "💬", "title": "About today's log", "text": n["text"]})
    return cards


@router.get("/report")
def doctor_report(user: UserDep, db: SessionDep, today: TodayDep, months: int = 6, notes: bool = False):
    """Data for the printable doctor's report (last `months` months)."""
    from ..report import build

    logs = db.exec(select(DayLog).where(DayLog.user_id == user.id, DayLog.day <= today)).all()
    return build(build_engine(db, user, today), logs, user, today, max(1, min(months, 24)), notes)


@router.get("/insights")
def insights(user: UserDep, db: SessionDep, today: TodayDep):
    eng = build_engine(db, user, today)
    logs = db.exec(select(DayLog).where(DayLog.user_id == user.id, DayLog.day <= today)).all()
    cur = eng.current
    temps = []
    if cur:
        temps = [
            {"date": l.day.isoformat(), "value": l.temperature}
            for l in sorted(logs, key=lambda x: x.day)
            if l.temperature and l.day >= cur.start
        ]
    weights = [
        {"date": l.day.isoformat(), "value": l.weight}
        for l in sorted(logs, key=lambda x: x.day)
        if l.weight and l.day >= today - D(days=180)
    ]
    return {
        "stats": eng.stats(),
        "flags": eng.flags(),
        "symptoms": symptom_patterns(eng, [(l.day, l.tags) for l in logs], LABELS),
        "heatmap": symptom_heatmap(eng, [(l.day, l.tags) for l in logs], LABELS),
        "temperature": temps,
        "weight": weights,
        "overview": eng.overview(),
    }


# ---------------------------------------------------------------- data ownership
@router.get("/export")
def export(user: UserDep, db: SessionDep):
    logs = db.exec(select(DayLog).where(DayLog.user_id == user.id).order_by(DayLog.day)).all()
    return {
        "app": "bloomery",
        "version": 1,
        "exported_at": now().isoformat(),
        "profile": public_user(user),
        "logs": [l.model_dump(mode="json", exclude={"user_id", "id"}) for l in logs],
    }


class ImportBody(BaseModel):
    logs: list[dict]
    replace: bool = False


@router.post("/import")
def import_data(body: ImportBody, user: UserDep, db: SessionDep):
    if body.replace:
        db.exec(delete(DayLog).where(DayLog.user_id == user.id))
    n = 0
    for raw in body.logs:
        d = date.fromisoformat(str(raw["day"]))
        data = LogIn.model_validate({k: raw.get(k) for k in LogIn.model_fields if raw.get(k) is not None})
        l = _get_log(db, user, d) or DayLog(user_id=user.id, day=d)
        for k, v in data.model_dump().items():
            setattr(l, k, v)
        db.add(l)
        n += 1
    db.commit()
    return {"imported": n}


class OtherImport(BaseModel):
    content: str = Field(max_length=20_000_000)


@router.post("/import/other")
def import_other(body: OtherImport, user: UserDep, db: SessionDep):
    """Period history from Flo / Clue / CSV. Never overwrites days you already logged as bleeding."""
    from ..importers import ImportFormatError, parse

    try:
        source, days = parse(body.content)
    except ImportFormatError as e:
        raise HTTPException(422, str(e)) from e
    if not days:
        raise HTTPException(422, f"Recognised a {source} file but found no period days in it.")
    periods = 0
    for d, e in days.items():
        if e.get("flow"):
            _set_flow(db, user, d, e["flow"])
            periods += 1
        if e.get("tags") or e.get("temperature"):
            db.flush()
            l = _get_log(db, user, d) or DayLog(user_id=user.id, day=d)
            tags = {c: set(v) for c, v in (l.tags or {}).items()}
            for c, vs in (e.get("tags") or {}).items():
                tags.setdefault(c, set()).update(vs)
            l.tags = {c: sorted(v) for c, v in tags.items()}
            if e.get("temperature") and not l.temperature:
                l.temperature = e["temperature"]
            db.add(l)
    db.commit()
    return {
        "source": source,
        "days": len(days),
        "period_days": periods,
        "first": min(days).isoformat(),
        "last": max(days).isoformat(),
    }


@router.delete("/account")
def delete_account(request: Request, user: UserDep, db: SessionDep):
    for m in (DayLog, ChatMessage, InsightCache):
        db.exec(delete(m).where(m.user_id == user.id))
    u = str(user.id)  # per-user settings: <kind>:<uid>, recap:<uid>:<start>, and token rows whose value is the uid
    db.exec(
        delete(Setting).where(
            Setting.key.like(f"%:{u}")
            | Setting.key.like(f"%:{u}:%")
            | (Setting.key.like("share:%") | Setting.key.like("ha:%") | Setting.key.like("api:%")) & (Setting.value == u)
        )
    )
    db.delete(user)
    db.commit()
    request.session.clear()
    return {"ok": True}
