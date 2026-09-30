"""Read-only partner sharing: a secret link showing cycle status + predictions. Never symptoms, moods, sex or notes.
Tokens live in the Setting table: share:<token> -> user id, shareof:<uid> -> token (one active link per user)."""
import secrets
from datetime import timedelta

from fastapi import APIRouter, HTTPException
from sqlmodel import Session

from ..deps import SessionDep, TodayDep, UserDep, build_engine
from ..models import Setting, User

router = APIRouter(prefix="/api/share", tags=["share"])

PARTNER_TIPS = {
    "menstrual": "Period days can mean cramps and low energy. A hot water bottle, snacks and taking a chore off her plate go a long way.",
    "follicular": "Energy usually climbs this week. A good time for plans, dates and doing active things together.",
    "fertile": "This is the fertile window, the days when pregnancy is most likely.",
    "ovulation": "Ovulation is estimated around today, the peak of the fertile window.",
    "luteal": "PMS can show up in this phase: tiredness, bloating or a shorter fuse. Extra patience and comfort food are appreciated.",
}


def _revoke(db: Session, uid: int) -> None:
    old = db.get(Setting, f"shareof:{uid}")
    if old:
        if s := db.get(Setting, f"share:{old.value}"):
            db.delete(s)
        db.delete(old)


@router.get("")
def get_link(user: UserDep, db: SessionDep):
    s = db.get(Setting, f"shareof:{user.id}")
    return {"token": s.value if s else None}


@router.post("")
def create_link(user: UserDep, db: SessionDep):
    """Creates a new link; any previous link stops working."""
    _revoke(db, user.id)
    token = secrets.token_urlsafe(18)
    db.add(Setting(key=f"share:{token}", value=str(user.id)))
    db.add(Setting(key=f"shareof:{user.id}", value=token))
    db.commit()
    return {"token": token}


@router.delete("")
def delete_link(user: UserDep, db: SessionDep):
    _revoke(db, user.id)
    db.commit()
    return {"ok": True}


@router.get("/{token}")
def view(token: str, db: SessionDep, today: TodayDep):
    """Public (token-gated) partner view."""
    s = db.get(Setting, f"share:{token}")
    user = db.get(User, int(s.value)) if s else None
    if not user:
        raise HTTPException(404, "This link is no longer active")
    eng = build_engine(db, user, today)
    ov = eng.overview()
    days = []
    for i in range(35):  # next 5 weeks: only cycle markers, no logs
        info = eng.day_info(today + timedelta(days=i))
        days.append({"date": info["date"], "kind": info["kind"]})
    phase = ov["status"].get("phase")
    return {
        "name": user.display_name or user.username,
        "today": ov["today"], "status": ov["status"], "current_cycle": ov["current_cycle"],
        "predicted_cycle_length": ov["predicted_cycle_length"], "next_period": ov["next_period"],
        "phase": phase, "tip": PARTNER_TIPS.get(phase or ""), "days": days,
    }
