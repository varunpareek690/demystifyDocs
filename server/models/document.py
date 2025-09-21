from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

class DocumentUpload(BaseModel):
    title: str
    content: str
    document_type: Optional[str] = "legal"

class DocumentHighlight(BaseModel):
    """Represents a highlighted section in a document."""
    text: str = Field(..., description="The highlighted text snippet")
    reason: Optional[str] = Field(None, description="Why this text is important")
    score: float = Field(..., ge=0, le=1, description="Relevance score 0-1")
    page_number: Optional[int] = Field(None, description="Page number if available")
    position: Optional[int] = Field(None, description="Character position in document")

class EnhancedDocumentSummary(BaseModel):
    """Enhanced document summary with highlights and detailed analysis."""
    document_id: str
    summary: str = Field(..., description="Main document summary")
    key_points: List[str] = Field(default_factory=list, description="Key points extracted")
    highlights: List[DocumentHighlight] = Field(default_factory=list, description="Important text highlights")
    complexity_score: int = Field(..., ge=1, le=10, description="Document complexity 1-10")
    important_dates: List[str] = Field(default_factory=list, description="Important dates mentioned")
    obligations: List[str] = Field(default_factory=list, description="User obligations")
    rights: List[str] = Field(default_factory=list, description="User rights")
    risks: List[str] = Field(default_factory=list, description="Potential risks or concerns")
    created_at: datetime
    
    # Statistics
    word_count: Optional[int] = Field(None, description="Original document word count")
    estimated_reading_time: Optional[int] = Field(None, description="Estimated reading time in minutes")

class FileUploadResponse(BaseModel):
    """Response from file upload with comprehensive processing results."""
    document_id: str
    filename: str
    title: str
    file_size: int
    file_type: str
    document_type: str
    blob_path: str = Field(..., description="GCS storage path")
    gcs_url: str = Field(..., description="GCS URL")
    content_type: str
    status: str = "success"
    message: str = "File uploaded and processed successfully"

class DocumentProcessingResult(BaseModel):
    """Complete result from document processing pipeline."""
    document: 'Document'
    summary: EnhancedDocumentSummary
    chat_session: Optional['ChatSession'] = None
    suggested_questions: List[str] = Field(default_factory=list)
    file_info: Dict[str, Any] = Field(default_factory=dict)
    processing_time_seconds: Optional[float] = None
    ai_processing_cost_estimate: Optional[float] = None

class Document(BaseModel):
    """Enhanced document model with GCS integration."""
    id: str
    title: str
    content: str
    filename: Optional[str] = None
    blob_path: Optional[str] = None
    gcs_url: Optional[str] = None
    file_size: Optional[int] = None
    file_type: Optional[str] = None
    content_type: Optional[str] = None
    document_type: str
    user_id: str
    created_at: datetime
    updated_at: datetime
    
    text_extracted: bool = Field(default=True, description="Whether text was successfully extracted")
    processing_status: str = Field(default="completed", description="Processing status")
    error_message: Optional[str] = None

class DocumentWithSummary(BaseModel):
    """Document with its AI-generated summary."""
    document: Document
    summary: Optional[EnhancedDocumentSummary] = None
    chat_sessions: List[Dict[str, Any]] = Field(default_factory=list)
    has_chat_sessions: bool = False

class DocumentHistoryItem(BaseModel):
    """Enhanced document history item with metadata."""
    document_id: str
    title: str
    filename: Optional[str]
    document_type: str
    file_type: Optional[str]
    file_size: Optional[int]
    uploaded_at: datetime
    updated_at: datetime
    has_gcs_file: bool = False
    
    summary: Optional[Dict[str, Any]] = None
    chat_info: Optional[Dict[str, Any]] = None
    processing_info: Optional[Dict[str, Any]] = None

DocumentSummary = EnhancedDocumentSummary

from models.chat import ChatSession
DocumentProcessingResult.model_rebuild()
DocumentWithSummary.model_rebuild()