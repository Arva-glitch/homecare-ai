from fastapi import APIRouter, Depends
from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.deps import get_current_user
from app.db.session import get_db
from app.models import ChatHistory, User
from app.schemas.common import Message
from app.schemas.misc import ChatMessageOut, ChatRequest, ChatResponse, ChatSession
from app.services.chat_service import answer

router = APIRouter(prefix="/chat", tags=["AI HomeCare Assistant"])


@router.post("", response_model=ChatResponse)
def send_message(payload: ChatRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    session_id, reply = answer(db, user, payload.message.strip(), payload.session_id)
    return ChatResponse(session_id=session_id, reply=ChatMessageOut.model_validate(reply),
                        llm_enabled=settings.llm_enabled)


@router.get("/status")
def chat_status(_: User = Depends(get_current_user)):
    return {"llm_enabled": settings.llm_enabled, "provider": settings.LLM_PROVIDER if settings.llm_enabled else None,
            "mode": "LLM" if settings.llm_enabled else "Rule-based fallback"}


@router.get("/sessions", response_model=list[ChatSession])
def sessions(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    rows = db.execute(
        select(ChatHistory.session_id, func.max(ChatHistory.created_at), func.count(ChatHistory.id),
               func.min(ChatHistory.id))
        .where(ChatHistory.user_id == user.id).group_by(ChatHistory.session_id)
        .order_by(func.max(ChatHistory.created_at).desc())
    ).all()
    out = []
    for sid, last, count, first_id in rows:
        first = db.get(ChatHistory, first_id)
        title = (first.message[:60] + ("…" if len(first.message) > 60 else "")) if first else "Conversation"
        out.append(ChatSession(session_id=sid, title=title, last_message_at=last, message_count=count))
    return out


@router.get("/history", response_model=list[ChatMessageOut])
def history(session_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    q = select(ChatHistory).where(ChatHistory.user_id == user.id, ChatHistory.session_id == session_id) \
        .order_by(ChatHistory.created_at, ChatHistory.id)
    return db.scalars(q).all()


@router.delete("/sessions/{session_id}", response_model=Message)
def delete_session(session_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    db.execute(delete(ChatHistory).where(ChatHistory.user_id == user.id, ChatHistory.session_id == session_id))
    db.commit()
    return Message(message="Conversation deleted")
