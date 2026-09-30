"""Token-gated read-only access: partner share links and Home Assistant / calendar feeds.
Never exposes symptoms, moods, sex or notes. Tokens live in the Setting table:
<kind>:<token> -> user id, <kind>of:<uid> -> token (one active token per kind per user)."""
import secrets
from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from sqlmodel import Session

from .. import VERSION
from ..deps import SessionDep, TodayDep, UserDep, build_engine
from ..models import Setting, User

router = APIRouter(tags=["share"])
KINDS = ("share", "ha")

PARTNER_TIPS = {
    "menstrual": "Period days can mean cramps and low energy. A hot water bottle, snacks and taking a chore off her plate go a long way.",
    "follicular": "Energy usually climbs this week. A good time for plans, dates and doing active things together.",
    "fertile": "This is the fertile window, the days when pregnancy is most likely.",
    "ovulation": "Ovulation is estimated around today, the peak of the fertile window.",
    "luteal": "PMS can show up in this phase: tiredness, bloating or a shorter fuse. Extra patience and comfort food are appreciated.",
}

PREGNANCY_TIP = "Pregnancy is hard work for the body. Help with meals, chores and appointments, and ask how she's feeling today."


# ---------------------------------------------------------------- token helpers
def _revoke(db: Session, kind: str, uid: int) -> None:
    old = db.get(Setting, f"{kind}of:{uid}")
    if old:
        if s := db.get(Setting, f"{kind}:{old.value}"):
            db.delete(s)
        db.delete(old)


def _owner(db: Session, kind: str, token: str) -> User:
    s = db.get(Setting, f"{kind}:{token}")
    user = db.get(User, int(s.value)) if s else None
    if not user:
        raise HTTPException(404, "This link is no longer active")
    return user


def _check(kind: str) -> str:
    if kind not in KINDS:
        raise HTTPException(404)
    return kind


@router.get("/api/tokens/{kind}")
def get_token(kind: str, user: UserDep, db: SessionDep):
    s = db.get(Setting, f"{_check(kind)}of:{user.id}")
    return {"token": s.value if s else None}


@router.post("/api/tokens/{kind}")
def create_token(kind: str, user: UserDep, db: SessionDep):
    """Creates a new token; any previous one of this kind stops working."""
    _revoke(db, _check(kind), user.id)
    token = secrets.token_urlsafe(18)
    db.add(Setting(key=f"{kind}:{token}", value=str(user.id)))
    db.add(Setting(key=f"{kind}of:{user.id}", value=token))
    db.commit()
    return {"token": token}


@router.delete("/api/tokens/{kind}")
def delete_token(kind: str, user: UserDep, db: SessionDep):
    _revoke(db, _check(kind), user.id)
    db.commit()
    return {"token": None}


# ---------------------------------------------------------------- partner view
@router.get("/api/share/{token}")
def partner_view(token: str, db: SessionDep, today: TodayDep):
    user = _owner(db, "share", token)
    eng = build_engine(db, user, today)
    ov = eng.overview()
    days = [{"date": (i := eng.day_info(today + timedelta(days=n)))["date"], "kind": i["kind"]} for n in range(35)]
    phase = ov["status"].get("phase")
    return {
        "name": user.display_name or user.username,
        "today": ov["today"], "status": ov["status"], "current_cycle": ov["current_cycle"],
        "predicted_cycle_length": ov["predicted_cycle_length"], "next_period": ov["next_period"],
        "phase": phase, "tip": PARTNER_TIPS.get(phase or "") or (PREGNANCY_TIP if ov["pregnancy"] else None), "days": days,
        "pregnancy": ov["pregnancy"],
    }


# ---------------------------------------------------------------- Home Assistant
def _local_today(tz: str | None) -> date:
    try:
        return datetime.now(ZoneInfo(tz)).date() if tz else date.today()
    except Exception:
        return date.today()


@router.get("/api/ha/{token}")
def ha_state(token: str, db: SessionDep, tz: str | None = None):
    """Flat JSON for Home Assistant REST sensors. `tz` = IANA zone so 'today' matches the user's day."""
    user = _owner(db, "ha", token)
    today = _local_today(tz)
    eng = build_engine(db, user, today)
    ov, st = eng.overview(), eng.status()
    cur = eng.current
    nxt = eng.next_period
    preg = ov["pregnancy"] or {}
    return {
        "user_id": user.id, "name": user.display_name or user.username, "version": VERSION,
        "mode": ov["mode"], "pregnancy_week": preg.get("week"), "due_date": preg.get("due"),
        "state": st.get("state"), "label": st.get("label"), "headline": st.get("headline"), "summary": st.get("sub"),
        "cycle_day": st.get("cycle_day"), "phase": st.get("phase"), "pregnancy_chance": st.get("chance"),
        "in_period": st.get("state") == "period", "fertile": st.get("phase") in ("fertile", "ovulation"),
        "days_until_period": (nxt - today).days if nxt else None, "next_period": ov["next_period"],
        "ovulation": cur.ovulation.isoformat() if cur else None,
        "cycle_length": ov["predicted_cycle_length"], "period_length": ov["predicted_period_length"],
        "today": today.isoformat(),
    }


def _ics_date(d: date) -> str:
    return d.strftime("%Y%m%d")


@router.get("/api/ha/{token}/calendar.ics")
def ha_calendar(token: str, db: SessionDep, tz: str | None = None):
    """iCalendar feed of predicted periods, fertile windows and ovulation (HA Remote Calendar, Apple/Google…)."""
    user = _owner(db, "ha", token)
    today = _local_today(tz)
    eng = build_engine(db, user, today)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    events = []
    for s in eng.segments:
        if s.end < today - timedelta(days=60):
            continue
        events.append(("Predicted period" if s.predicted else "Period", s.start, s.period_end))
        events.append(("Fertile window", s.fertile_start, s.fertile_end))
        events.append(("Ovulation (estimated)", s.ovulation, s.ovulation))
    lines = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//Bloomery//Cycle//EN", "X-WR-CALNAME:Bloomery", "CALSCALE:GREGORIAN"]
    for title, a, b in events:
        lines += ["BEGIN:VEVENT", f"UID:{title.split()[0].lower()}-{a.isoformat()}@bloomery", f"DTSTAMP:{stamp}",
                  f"DTSTART;VALUE=DATE:{_ics_date(a)}", f"DTEND;VALUE=DATE:{_ics_date(b + timedelta(days=1))}",
                  f"SUMMARY:{title}", "TRANSP:TRANSPARENT", "END:VEVENT"]
    lines.append("END:VCALENDAR")
    return Response("\r\n".join(lines) + "\r\n", media_type="text/calendar; charset=utf-8")
