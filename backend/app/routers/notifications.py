from typing import Literal
from urllib.parse import urlsplit
from zoneinfo import ZoneInfo

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field, field_validator

from .. import notify, push
from ..deps import SessionDep, TodayDep, UserDep
from ..i18n import _

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
    devices = len(push.subscriptions(db, user.id))
    if not body.url and not devices:
        raise HTTPException(400, _("Turn on notifications for this device or enter a notification URL first"))
    msg = notify.compose(db, user, today, body.kinds) or (
        "🌸 " + _("Bloomery is connected"),
        _("Notifications work! You'll hear from me when there's something worth knowing."),
    )
    if body.url:
        try:
            await notify.send(body.url, *msg)
        except Exception as e:
            return {"ok": False, "error": f"{e.__class__.__name__}: {e}"[:300]}
    pushed = await push.send(db, user.id, *msg) if devices else 0
    if devices and not pushed and not body.url:
        return {
            "ok": False,
            "error": "Your device didn't accept the notification. Turn device notifications off and on again.",
        }
    return {"ok": True, "title": msg[0], "devices": pushed}


# ---------------------------------------------------------------- Web Push devices
class PushKeys(BaseModel):
    p256dh: str = Field(max_length=200)
    auth: str = Field(max_length=100)


class PushSub(BaseModel):
    endpoint: str = Field(max_length=1000, pattern=r"^https://")
    keys: PushKeys


@router.get("/push")
def push_info(user: UserDep, db: SessionDep):
    return {"public_key": push.public_key(db), "devices": len(push.subscriptions(db, user.id))}


@router.post("/push")
def push_subscribe(body: PushSub, request: Request, user: UserDep, db: SessionDep):
    subs = [s for s in push.subscriptions(db, user.id) if s["endpoint"] != body.endpoint]
    origin = urlsplit(request.headers.get("origin", ""))
    contact = f"https://{origin.hostname}" if origin.scheme == "https" and origin.hostname else ""
    subs = [*subs, {**body.model_dump(), "contact": contact}][-10:]  # ponytail: newest 10 devices per user
    push.save_subscriptions(db, user.id, subs)
    return {"devices": len(subs)}


@router.delete("/push")
def push_unsubscribe(endpoint: str, user: UserDep, db: SessionDep):
    subs = [s for s in push.subscriptions(db, user.id) if s["endpoint"] != endpoint]
    push.save_subscriptions(db, user.id, subs)
    return {"devices": len(subs)}
