import json
from datetime import date
from typing import Annotated

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from fastapi import Depends, HTTPException, Query, Request
from sqlmodel import Session, select

from . import contraception
from .cycles import Engine, Profile
from .db import get_session
from .models import BLEEDING, DayLog, Setting, User

ph = PasswordHasher()
SessionDep = Annotated[Session, Depends(get_session)]


def hash_pw(pw: str) -> str:
    return ph.hash(pw)


def verify_pw(h: str, pw: str) -> bool:
    try:
        return ph.verify(h, pw)
    except VerifyMismatchError:
        return False


def current_user(request: Request, db: SessionDep) -> User:
    uid = request.session.get("uid")
    user = db.get(User, uid) if uid else None
    if not user:
        raise HTTPException(401, "Not authenticated")
    return user


UserDep = Annotated[User, Depends(current_user)]


def today_param(today: date | None = Query(None, description="Client's local date")) -> date:
    return today or date.today()


TodayDep = Annotated[date, Depends(today_param)]


def life_stage(db: Session, uid: int) -> dict:
    """{'mode': 'cycle'|'pregnancy'|'perimenopause', 'lmp': iso date | None} from Setting mode:<uid>."""
    s = db.get(Setting, f"mode:{uid}")
    return json.loads(s.value) if s else {"mode": "cycle", "lmp": None}


def bc_config(db: Session, uid: int) -> dict | None:
    """Birth control settings (Setting bc:<uid>), see contraception.py."""
    s = db.get(Setting, f"bc:{uid}")
    return json.loads(s.value) if s else None


def build_engine(db: Session, user: User, today: date) -> Engine:
    st = life_stage(db, user.id)
    logs = db.exec(select(DayLog).where(DayLog.user_id == user.id)).all()
    return Engine(
        Profile(
            user.cycle_length,
            user.period_length,
            user.luteal_length,
            user.goal,
            st["mode"],
            date.fromisoformat(st["lmp"]) if st.get("lmp") else None,
            contraception.hormonal(bc_config(db, user.id)),
        ),
        today,
        [l.day for l in logs if l.flow in BLEEDING],
        {l.day: l.temperature for l in logs if l.temperature},
    )
