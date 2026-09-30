from datetime import date
from typing import Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from fastapi.responses import StreamingResponse
from sqlmodel import Session, delete, func, select

from .. import ai
from ..db import get_engine
from ..deps import SessionDep, TodayDep, UserDep, build_engine
from ..feed import cycle_summary
from ..models import ChatMessage, DayLog, InsightCache, Setting, User

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


@router.get("/recap")
async def recap(start: date, user: UserDep, db: SessionDep, today: TodayDep, refresh: bool = False):
    """AI recap of the cycle starting on `start` (rules fallback). Completed cycles are cached."""
    eng = build_engine(db, user, today)
    seg = next((s for s in eng.segments if s.start == start and not s.predicted), None)
    if not seg:
        raise HTTPException(404, "No logged cycle starts on that date")
    logs = _logs(db, user)
    done = seg.end < today and seg is not eng.current
    base = {"start": seg.start.isoformat(), "length": seg.length if done else None, "complete": done}
    if not ai.enabled():
        return {**base, "source": "rules", "content": cycle_summary(eng, logs, seg)}
    key = f"recap:{user.id}:{seg.start.isoformat()}"
    cached = db.get(Setting, key)
    if cached and done and not refresh:
        return {**base, "source": "ai", "content": cached.value, "cached": True}
    try:
        text = await ai.complete(ai.SYSTEM + "\n\nCYCLE DATA (JSON):\n" + ai.recap_context(eng, logs, seg),
                                 [{"role": "user", "content": ai.RECAP_PROMPT}], max_tokens=450)
    except ai.AIError as e:
        return {**base, "source": "rules", "content": cycle_summary(eng, logs, seg), "error": str(e)}
    if done:
        db.merge(Setting(key=key, value=text))
        db.commit()
    return {**base, "source": "ai", "content": text}


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


@router.post("/chat/stream")
async def chat_stream(body: ChatIn, user: UserDep, db: SessionDep, today: TodayDep):
    """Same as /chat but streams the reply as plain-text chunks; saves both messages when done."""
    if not ai.enabled():
        raise HTTPException(503, "AI is disabled on this server. Enable it in Profile → AI assistant.")
    eng = build_engine(db, user, today)
    prev = db.exec(select(ChatMessage).where(ChatMessage.user_id == user.id)
                   .order_by(ChatMessage.id.desc()).limit(12)).all()[::-1]
    msgs = [{"role": m.role, "content": m.content} for m in prev] + [{"role": "user", "content": body.message}]
    system = ai.SYSTEM + "\n\nUSER DATA (JSON):\n" + ai.build_context(eng, _logs(db, user), user)
    uid = user.id

    async def gen():
        parts: list[str] = []
        try:
            async for chunk in ai.stream(system, msgs):
                parts.append(chunk)
                yield chunk
        except ai.AIError as e:
            yield f"{chr(10) * 2 if parts else ''}⚠️ {e}"
            return
        reply = ai._THINK.sub("", "".join(parts)).strip()
        with Session(get_engine()) as s:  # request-scoped session may already be closed while streaming
            s.add(ChatMessage(user_id=uid, role="user", content=body.message))
            s.add(ChatMessage(user_id=uid, role="assistant", content=reply))
            s.commit()

    return StreamingResponse(gen(), media_type="text/plain; charset=utf-8", headers={"X-Accel-Buffering": "no"})


@router.delete("/chat")
def clear(user: UserDep, db: SessionDep):
    db.exec(delete(ChatMessage).where(ChatMessage.user_id == user.id))
    db.commit()
    return {"ok": True}
