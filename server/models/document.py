from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class DocumentUpload(BaseModel):
    title: str
    content: str
    document_type: Optional[str] = "legal"

class FileUploadResponse(BaseModel):
    document_id: str
    filename: str
    title: str
    file_size: int
    file_type: str
    document_type: str
    stored_filename: Optional[str] = None  # New field for local storage
    file_path: Optional[str] = None  # New field for local storage
    status: str
    message: str

class DocumentSummary(BaseModel):
    document_id: str
    summary: str
    key_points: List[str]
    complexity_score: int
    important_dates: List[str] = []
    obligations: List[str] = []
    rights: List[str] = []
    created_at: datetime

class Document(BaseModel):
    id: str
    title: str
    content: str
    filename: Optional[str] = None
    stored_filename: Optional[str] = None  # New field for local storage
    file_path: Optional[str] = None  # New field for local storage
    file_size: Optional[int] = None
    file_type: Optional[str] = None
    document_type: str
    user_id: str
    created_at: datetime
    updated_at: datetime
    summary: Optional[DocumentSummary] = None

class DocumentWithSummary(BaseModel):
    document: Document
    summary: Optional[DocumentSummary] = None
