from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from sqlmodel import delete, select

from .. import ai
from ..deps import SessionDep, TodayDep, UserDep, build_engine
from ..models import ChatMessage, DayLog, InsightCache

router = APIRouter(prefix="/api/ai", tags=["ai"])


@router.get("/status")
def status():
    return ai.info()


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
