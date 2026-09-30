from typing import Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from sqlmodel import delete, func, select

from .. import ai
from ..deps import SessionDep, TodayDep, UserDep, build_engine
from ..models import ChatMessage, DayLog, InsightCache, User

router = APIRouter(prefix="/api/ai", tags=["ai"])


@router.get("/status")
def status():
    return ai.info()


# ---------------------------------------------------------------- in-app configuration (admin = first account)
def require_admin(user: User, db) -> None:
    if user.id != db.exec(select(func.min(User.id))).one():
        raise HTTPException(403, "Only the server owner (first account) can change AI settings")


class ConfigIn(BaseModel):
    provider: Literal["none", "anthropic", "openai", "openrouter", "ollama", "custom"]
    base_url: str | None = Field(None, max_length=500)
    model: str | None = Field(None, max_length=200)
    api_key: str | None = Field(None, max_length=500)  # None = keep stored key, "" = clear


def _public(cfg: dict) -> dict:
    k = cfg.pop("api_key")
    return {**cfg, "has_key": bool(k), "key_hint": k[-4:] if len(k) > 8 else "",
            "providers": {p: {"base_url": b, "model": m} for p, (b, m) in ai.PROVIDERS.items()}}


@router.get("/config")
def get_config(user: UserDep, db: SessionDep):
    require_admin(user, db)
    return _public(ai.config())


@router.put("/config")
def put_config(body: ConfigIn, user: UserDep, db: SessionDep):
    require_admin(user, db)
    ai.save(body.model_dump())
    return _public(ai.config())


@router.post("/config/test")
async def test_config(body: ConfigIn, user: UserDep, db: SessionDep):
    """Try unsaved settings (falls back to the stored key when api_key is omitted)."""
    require_admin(user, db)
    try:
        reply = await ai.complete("Reply with exactly: OK", [{"role": "user", "content": "ping"}],
                                  max_tokens=20, cfg=ai.config(body.model_dump()))
        return {"ok": True, "reply": reply[:200]}
    except ai.AIError as e:
        return {"ok": False, "error": str(e)}


def _logs(db, user):
    return db.exec(select(DayLog).where(DayLog.user_id == user.id)).all()


@router.get("/daily")
async def daily(user: UserDep, db: SessionDep, today: TodayDep, refresh: bool = False):
    eng = build_engine(db, user, today)
    if not ai.enabled() or not eng.periods:
        return {"source": "rules", "content": ai.fallback_insight(eng)}
    cached = db.exec(select(InsightCache).where(InsightCache.user_id == user.id, InsightCache.day == today)).first()
    if cached and not refresh:
        return {"source": "ai", "content": cached.content, "cached": True}
    try:
        text = await ai.complete(
            ai.SYSTEM + "\n\nUSER DATA (JSON):\n" + ai.build_context(eng, _logs(db, user), user),
            [{"role": "user", "content": ai.daily_prompt(today)}], max_tokens=400)
    except ai.AIError as e:
        return {"source": "rules", "content": ai.fallback_insight(eng), "error": str(e)}
    if cached:
        cached.content = text
    else:
        cached = InsightCache(user_id=user.id, day=today, content=text)
    db.add(cached)
    db.commit()
    return {"source": "ai", "content": text}


class ChatIn(BaseModel):
    message: str = Field(min_length=1, max_length=4000)


@router.get("/chat")
def history(user: UserDep, db: SessionDep):
    rows = db.exec(select(ChatMessage).where(ChatMessage.user_id == user.id).order_by(ChatMessage.id)).all()
    return [{"role": r.role, "content": r.content, "created_at": r.created_at} for r in rows[-100:]]


@router.post("/chat")
async def chat(body: ChatIn, user: UserDep, db: SessionDep, today: TodayDep):
    if not ai.enabled():
        raise HTTPException(503, "AI is disabled on this server. Set BLOOMERY_AI_PROVIDER to enable it.")
    eng = build_engine(db, user, today)
    prev = db.exec(select(ChatMessage).where(ChatMessage.user_id == user.id)
                   .order_by(ChatMessage.id.desc()).limit(12)).all()[::-1]
    msgs = [{"role": m.role, "content": m.content} for m in prev] + [{"role": "user", "content": body.message}]
    try:
        reply = await ai.complete(
            ai.SYSTEM + "\n\nUSER DATA (JSON):\n" + ai.build_context(eng, _logs(db, user), user), msgs)
    except ai.AIError as e:
        raise HTTPException(502, str(e)) from e
    db.add(ChatMessage(user_id=user.id, role="user", content=body.message))
    db.add(ChatMessage(user_id=user.id, role="assistant", content=reply))
    db.commit()
    return {"role": "assistant", "content": reply}


@router.delete("/chat")
def clear(user: UserDep, db: SessionDep):
    db.exec(delete(ChatMessage).where(ChatMessage.user_id == user.id))
    db.commit()
    return {"ok": True}
