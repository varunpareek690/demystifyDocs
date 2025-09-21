from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
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
    metadata: Optional[Dict[str, Any]] = None
    
    token_count: Optional[int] = Field(None, description="Approximate token count")
    processing_time_ms: Optional[int] = Field(None, description="AI processing time in milliseconds")

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
    
    total_ai_responses: Optional[int] = Field(None, description="Number of AI responses")
    last_activity: Optional[datetime] = Field(None, description="Last message timestamp")

class SendMessageRequest(BaseModel):
    message: str
    
    include_full_context: bool = Field(True, description="Include full document context")
    max_context_chunks: int = Field(3, ge=1, le=10, description="Maximum document chunks to include")

class SendMessageResponse(BaseModel):
    """Enhanced response for message sending."""
    user_message: ChatMessage
    ai_message: ChatMessage
    session_updated: ChatSession
    message_count: int
    
    context_chunks_used: Optional[int] = None
    processing_time_seconds: Optional[float] = None
    ai_confidence_score: Optional[float] = Field(None, ge=0, le=1)

class ChatSessionWithMessages(BaseModel):
    """Chat session with full message history and context."""
    session: ChatSession
    messages: List[ChatMessage]
    document_title: str
    document_summary: Optional[str] = None
    
    suggested_questions: List[str] = Field(default_factory=list)
    message_count: int = 0
    user_message_count: int = 0
    conversation_topics: List[str] = Field(default_factory=list, description="Detected conversation topics")

class ChatHistoryItem(BaseModel):
    """Enhanced chat history item with preview and metadata."""
    id: str
    title: str
    document_id: str
    message_count: int
    created_at: datetime
    updated_at: datetime
    is_active: bool
    
    preview: Optional[Dict[str, Any]] = None
    document_title: Optional[str] = None
    complexity_indicator: Optional[str] = None

class ChatExportData(BaseModel):
    """Data structure for chat exports."""
    export_data: str
    format: str
    session_id: str
    message_count: int
    export_timestamp: datetime = Field(default_factory=datetime.utcnow)
    file_size_bytes: Optional[int] = None

class ChatStats(BaseModel):
    """User's chat usage statistics."""
    total_sessions: int
    total_messages: int
    active_sessions: int
    recent_activity_7days: int
    average_messages_per_session: float
    most_active_session: Optional[Dict[str, Any]] = None
    
    this_week_messages: Optional[int] = None
    this_month_sessions: Optional[int] = None
    avg_session_duration_minutes: Optional[float] = None

class SuggestedQuestions(BaseModel):
    """AI-generated suggested questions for a document/session."""
    questions: List[str]
    session_id: str
    document_id: str
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    relevance_scores: Optional[List[float]] = None

class ChatResponse(BaseModel):
    message: ChatMessage
    session: ChatSession

class ChatHistoryResponse(BaseModel):
    sessions: List[ChatHistoryItem]
    total_sessions: int
    showing_limit: Optional[int] = None
    has_more: bool = False

class EnhancedChatSessionResponse(BaseModel):
    """Complete response for getting a chat session."""
    session: ChatSessionWithMessages
    suggested_questions: List[str] = Field(default_factory=list)
    message_count: int
    user_message_count: int
    
    document_info: Optional[Dict[str, Any]] = None
    processing_stats: Optional[Dict[str, Any]] = None