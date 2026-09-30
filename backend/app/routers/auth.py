import time
from collections import defaultdict, deque

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field
from sqlmodel import func, select

from ..config import get_settings
from ..deps import SessionDep, UserDep, hash_pw, verify_pw
from ..models import User

router = APIRouter(prefix="/api/auth", tags=["auth"])


class Credentials(BaseModel):
    username: str = Field(min_length=2, max_length=64)
    password: str = Field(min_length=8, max_length=256)
    display_name: str = ""


def registration_open(db) -> bool:
    mode = get_settings().allow_registration.lower()
    if mode == "true":
        return True
    if mode == "false":
        return False
    return db.exec(select(func.count()).select_from(User)).one() == 0


def public_user(u: User) -> dict:
    return u.model_dump(exclude={"password_hash"})


@router.get("/status")
def status(request: Request, db: SessionDep):
    return {"registration_open": registration_open(db), "authenticated": bool(request.session.get("uid"))}


@router.post("/register")
def register(body: Credentials, request: Request, db: SessionDep):
    if not registration_open(db):
        raise HTTPException(403, "Registration is closed")
    uname = body.username.strip().lower()
    if db.exec(select(User).where(User.username == uname)).first():
        raise HTTPException(409, "Username taken")
    u = User(username=uname, password_hash=hash_pw(body.password), display_name=body.display_name or body.username)
    db.add(u)
    db.commit()
    db.refresh(u)
    request.session["uid"] = u.id
    return public_user(u)


# ponytail: in-memory, per process (we run 1 worker); resets on restart, which is fine for brute-force damping
FAILS: dict[str, deque] = defaultdict(deque)
WINDOW, MAX_FAILS = 15 * 60, 10


def _throttled(*keys: str) -> bool:
    now = time.monotonic()
    for k in keys:
        q = FAILS[k]
        while q and now - q[0] > WINDOW:
            q.popleft()
        if len(q) >= MAX_FAILS:
            return True
    return False


@router.post("/login")
def login(body: Credentials, request: Request, db: SessionDep):
    uname = body.username.strip().lower()
    # per-IP only: a per-username limit would let strangers lock the owner out of an internet-facing instance
    keys = (f"ip:{request.client.host if request.client else '?'}",)
    if _throttled(*keys):
        raise HTTPException(429, "Too many failed attempts. Try again in 15 minutes.")
    u = db.exec(select(User).where(User.username == uname)).first()
    if not u or not verify_pw(u.password_hash, body.password):
        for k in keys:
            FAILS[k].append(time.monotonic())
        raise HTTPException(401, "Invalid username or password")
    for k in keys:
        FAILS.pop(k, None)
    request.session["uid"] = u.id
    return public_user(u)


@router.post("/logout")
def logout(request: Request):
    request.session.clear()
    return {"ok": True}


@router.get("/me")
def me(user: UserDep):
    return public_user(user)


class PasswordChange(BaseModel):
    current: str
    new: str = Field(min_length=8, max_length=256)


@router.post("/password")
def change_password(body: PasswordChange, user: UserDep, db: SessionDep):
    if not verify_pw(user.password_hash, body.current):
        raise HTTPException(400, "Current password is wrong")
    user.password_hash = hash_pw(body.new)
    db.add(user)
    db.commit()
    return {"ok": True}
