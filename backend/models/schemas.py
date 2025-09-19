from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class DocumentType(str, Enum):
    PDF = "pdf"
    DOCX = "docx"
    TXT = "txt"
    MD = "md"
    PPTX = "pptx"
    IMAGE = "image"


class DocumentUpload(BaseModel):
    filename: str
    content_type: str
    file_size: int


class DocumentMetadata(BaseModel):
    page: Optional[int] = None
    bbox: Optional[Dict[str, float]] = None
    chunk_id: str
    document_id: str


class DocumentResponse(BaseModel):
    id: str
    filename: str
    document_type: DocumentType
    file_size: int
    chunks_count: int
    created_at: datetime
    metadata: Optional[Dict[str, Any]] = None


class ChatMessage(BaseModel):
    role: str = Field(..., description="Either 'user' or 'assistant'")
    content: str
    citations: Optional[List[Dict[str, Any]]] = None


class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None
    include_citations: bool = True
    max_results: int = 5
    temperature: float = 0.7


class Citation(BaseModel):
    text: str
    document_id: str
    document_name: str
    page: Optional[int] = None
    bbox: Optional[Dict[str, float]] = None
    confidence: float


class ChatResponse(BaseModel):
    response: str
    conversation_id: str
    citations: List[Citation]
    tokens_used: Optional[int] = None
    response_time_ms: float


class SearchQuery(BaseModel):
    query: str
    limit: int = 10
    document_ids: Optional[List[str]] = None
    min_score: float = 0.7


class SearchResult(BaseModel):
    text: str
    document_id: str
    document_name: str
    score: float
    metadata: DocumentMetadata


class HealthCheck(BaseModel):
    status: str = "healthy"
    version: str
    vector_db_connected: bool
    llm_available: bool
    timestamp: datetime = Field(default_factory=datetime.utcnow)