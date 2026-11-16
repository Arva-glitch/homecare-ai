from datetime import datetime

from pydantic import BaseModel, Field

from app.utils.time import UTCDateTime
from app.schemas.common import ORMModel


class NotificationOut(ORMModel):
    id: int
    type: str
    severity: str
    title: str
    message: str
    link: str | None
    is_read: bool
    created_at: UTCDateTime


class NotificationList(BaseModel):
    items: list[NotificationOut]
    unread_count: int


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)
    session_id: str | None = Field(default=None, max_length=64)


class ChatMessageOut(ORMModel):
    id: int
    session_id: str
    role: str
    message: str
    source: str | None
    created_at: UTCDateTime


class ChatResponse(BaseModel):
    session_id: str
    reply: ChatMessageOut
    llm_enabled: bool


class ChatSession(BaseModel):
    session_id: str
    title: str
    last_message_at: UTCDateTime
    message_count: int
