from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum

class MessageRole(str, Enum):
    USER = "user"
    AI = "ai"
    SYSTEM = "system"

class ChatMessage(BaseModel):
    id: str
    chat_session_id: str
    role: MessageRole
    content: str
    timestamp: datetime
    metadata: Optional[dict] = None

class ChatSessionCreate(BaseModel):
    document_id: str
    title: Optional[str] = None

class ChatSession(BaseModel):
    id: str
    user_id: str
    document_id: str
    title: str
    created_at: datetime
    updated_at: datetime
    message_count: int = 0
    is_active: bool = True

class SendMessageRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    message: ChatMessage
    session: ChatSession

class ChatHistoryResponse(BaseModel):
    sessions: List[ChatSession]
    total_sessions: int

class ChatSessionWithMessages(BaseModel):
    session: ChatSession
    messages: List[ChatMessage]
    document_title: str
    document_summary: Optional[str] = None