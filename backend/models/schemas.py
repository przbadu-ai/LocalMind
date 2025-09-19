"""
Pydantic models for request/response schemas.

This module defines all the data models used for API requests and responses,
ensuring type safety and automatic validation throughout the application.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class DocumentType(str, Enum):
    """
    Enumeration of supported document types.

    Attributes:
        PDF: Adobe PDF documents
        DOCX: Microsoft Word documents
        TXT: Plain text files
        MD: Markdown files
        PPTX: Microsoft PowerPoint presentations
        IMAGE: Image files (PNG, JPG, JPEG)
    """
    PDF = "pdf"
    DOCX = "docx"
    TXT = "txt"
    MD = "md"
    PPTX = "pptx"
    IMAGE = "image"


class DocumentUpload(BaseModel):
    """
    Schema for document upload metadata.

    Attributes:
        filename: Original name of the uploaded file
        content_type: MIME type of the file
        file_size: Size of the file in bytes
    """
    filename: str
    content_type: str
    file_size: int


class DocumentMetadata(BaseModel):
    """
    Metadata for document chunks with position tracking.

    Attributes:
        page: Page number where the chunk appears (1-indexed)
        bbox: Bounding box coordinates {x0, y0, x1, y1} for exact text location
        chunk_id: Unique identifier for this specific chunk
        document_id: Reference to the parent document
    """
    page: Optional[int] = Field(None, description="Page number (1-indexed)")
    bbox: Optional[Dict[str, float]] = Field(
        None,
        description="Bounding box coordinates for text location"
    )
    chunk_id: str = Field(..., description="Unique chunk identifier")
    document_id: str = Field(..., description="Parent document ID")


class DocumentResponse(BaseModel):
    """
    Response model for document information.

    Attributes:
        id: Unique document identifier (SHA256 hash)
        filename: Original filename
        document_type: Type of document (PDF, DOCX, etc.)
        file_size: Size in bytes
        chunks_count: Number of chunks after processing
        created_at: Timestamp when document was uploaded
        metadata: Additional document metadata
    """
    id: str = Field(..., description="Unique document ID")
    filename: str = Field(..., description="Original filename")
    document_type: DocumentType
    file_size: int = Field(..., description="File size in bytes")
    chunks_count: int = Field(..., description="Number of text chunks")
    created_at: datetime = Field(..., description="Upload timestamp")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class ChatMessage(BaseModel):
    """
    Individual message in a chat conversation.

    Attributes:
        role: Message sender role ('user' or 'assistant')
        content: Text content of the message
        citations: Optional list of source citations
    """
    role: str = Field(..., pattern="^(user|assistant)$", description="Sender role")
    content: str = Field(..., description="Message content")
    citations: Optional[List[Dict[str, Any]]] = Field(
        None,
        description="Source citations for this message"
    )


class ChatRequest(BaseModel):
    """
    Request model for chat interactions.

    Attributes:
        message: User's input message
        conversation_id: Optional ID to continue existing conversation
        include_citations: Whether to include source citations in response
        max_results: Maximum number of context chunks to retrieve
        temperature: LLM temperature for response generation (0.0-1.0)
    """
    message: str = Field(..., min_length=1, description="User message")
    conversation_id: Optional[str] = Field(None, description="Existing conversation ID")
    include_citations: bool = Field(True, description="Include source citations")
    max_results: int = Field(5, ge=1, le=20, description="Max context chunks")
    temperature: float = Field(0.7, ge=0.0, le=1.0, description="LLM temperature")


class Citation(BaseModel):
    """
    Citation information for source attribution.

    Attributes:
        text: Excerpt from the source document
        document_id: Unique identifier of the source document
        document_name: Human-readable name of the source document
        page: Page number where the citation appears
        bbox: Bounding box for exact location in document
        confidence: Relevance score (0.0-1.0)
    """
    text: str = Field(..., description="Source text excerpt")
    document_id: str = Field(..., description="Source document ID")
    document_name: str = Field(..., description="Source document name")
    page: Optional[int] = Field(None, description="Page number in source")
    bbox: Optional[Dict[str, float]] = Field(None, description="Text location coordinates")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Relevance score")


class ChatResponse(BaseModel):
    """
    Response model for chat interactions.

    Attributes:
        response: Generated response text
        conversation_id: ID for conversation continuity
        citations: List of source citations
        tokens_used: Number of tokens consumed (for billing/limits)
        response_time_ms: Processing time in milliseconds
    """
    response: str = Field(..., description="Generated response")
    conversation_id: str = Field(..., description="Conversation ID for continuity")
    citations: List[Citation] = Field(default_factory=list, description="Source citations")
    tokens_used: Optional[int] = Field(None, description="Token consumption")
    response_time_ms: float = Field(..., description="Response generation time (ms)")


class SearchQuery(BaseModel):
    """
    Query parameters for semantic search.

    Attributes:
        query: Search query text
        limit: Maximum number of results to return
        document_ids: Optional filter by specific documents
        min_score: Minimum similarity score threshold (0.0-1.0)
    """
    query: str = Field(..., min_length=1, description="Search query")
    limit: int = Field(10, ge=1, le=100, description="Max results")
    document_ids: Optional[List[str]] = Field(None, description="Filter by documents")
    min_score: float = Field(0.7, ge=0.0, le=1.0, description="Minimum similarity")


class SearchResult(BaseModel):
    """
    Individual search result with metadata.

    Attributes:
        text: Matching text chunk
        document_id: Source document identifier
        document_name: Human-readable document name
        score: Similarity score (0.0-1.0)
        metadata: Additional chunk metadata
    """
    text: str = Field(..., description="Matching text")
    document_id: str = Field(..., description="Source document ID")
    document_name: str = Field(..., description="Source document name")
    score: float = Field(..., ge=0.0, le=1.0, description="Similarity score")
    metadata: DocumentMetadata = Field(..., description="Chunk metadata")


class HealthCheck(BaseModel):
    """
    Health check response model.

    Attributes:
        status: Current health status ('healthy' or 'unhealthy')
        version: Application version
        vector_db_connected: Vector database connection status
        llm_available: LLM service availability
        timestamp: Check timestamp
    """
    status: str = Field(default="healthy", pattern="^(healthy|unhealthy)$")
    version: str = Field(..., description="Application version")
    vector_db_connected: bool = Field(..., description="Vector DB status")
    llm_available: bool = Field(..., description="LLM service status")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(datetime.timezone.utc),
        description="Health check timestamp"
    )