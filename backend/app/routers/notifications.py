from typing import Literal
from zoneinfo import ZoneInfo

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, field_validator

from .. import notify
from ..deps import SessionDep, TodayDep, UserDep

router = APIRouter(prefix="/api/notifications", tags=["notifications"])


class NotifyIn(BaseModel):
    url: str = Field("", max_length=500)
    time: str = Field("08:00", pattern=r"^([01]\d|2[0-3]):[0-5]\d$")
    tz: str = "UTC"
    kinds: list[Literal["milestone", "forecast", "recap", "tip", "pill"]] = []

    @field_validator("url")
    @classmethod
    def _http(cls, v: str) -> str:
        if v and not v.startswith(("http://", "https://")):
            raise ValueError("URL must start with http:// or https://")
        return v.strip()

    @field_validator("tz")
    @classmethod
    def _tz(cls, v: str) -> str:
        try:
            ZoneInfo(v)
        except Exception as e:  # ZoneInfoNotFoundError is a KeyError, which pydantic won't turn into a 422
            raise ValueError(f"unknown time zone {v!r}") from e
        return v


@router.get("")
def get(user: UserDep, db: SessionDep):
    return {k: v for k, v in notify.load(db, user.id).items() if k != "last"}


@router.put("")
def put(body: NotifyIn, user: UserDep, db: SessionDep):
    cfg = {**notify.load(db, user.id), **body.model_dump()}
    notify.store(db, user.id, cfg)
    return {k: v for k, v in cfg.items() if k != "last"}


@router.post("/test")
async def test(body: NotifyIn, user: UserDep, db: SessionDep, today: TodayDep):
    """Send what today's notification would contain (or a hello if there's nothing today)."""
    if not body.url:
        raise HTTPException(400, "Enter a notification URL first")
    msg = notify.compose(db, user, today, body.kinds) or (
        "🌸 Bloomery is connected", "Notifications work! You'll hear from me when there's something worth knowing.")
    try:
        await notify.send(body.url, *msg)
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "error": f"{e.__class__.__name__}: {e}"[:300]}
    return {"ok": True, "title": msg[0]}
