from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class DocumentUpload(BaseModel):
    title: str
    content: str
    document_type: Optional[str] = "legal"

class DocumentSummary(BaseModel):
    document_id: str
    summary: str
    key_points: List[str]
    complexity_score: int
    created_at: datetime

class Document(BaseModel):
    id: str
    title: str
    content: str
    document_type: str
    user_id: str
    created_at: datetime
    updated_at: datetime
    summary: Optional[DocumentSummary] = None
