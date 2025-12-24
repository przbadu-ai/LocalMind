"""Document upload and management API endpoints."""

import logging
import os
import tempfile
import uuid
from typing import Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel

from database.models import Document
from database.repositories.document_repository import (
    DocumentChunkRepository,
    DocumentRepository,
)
from services.document_service import document_service

logger = logging.getLogger(__name__)

router = APIRouter()

# Configuration
MAX_FILE_SIZE_MB = 50
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024
ALLOWED_MIME_TYPES = [
    "application/pdf",
    # Office documents
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",  # docx
    "application/vnd.openxmlformats-officedocument.presentationml.presentation", # pptx
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",         # xlsx
    "application/vnd.ms-excel",                                                   # xls
    "application/vnd.ms-powerpoint",                                             # ppt
    "application/msword",                                                      # doc
    # Web/Text formats
    "text/html",
    "text/markdown",
    "text/x-markdown",
    "text/plain",
    "text/asciidoc",
    "application/rtf",
    "application/xml",
    "text/xml",
    # Media formats
    "image/png",
    "image/jpeg",
    "image/webp",
    "image/gif",
    "image/tiff",
    "image/bmp",
    "audio/mpeg",
    "audio/wav",
    "audio/ogg",
    "audio/mp4",
]


class DocumentResponse(BaseModel):
    """Response model for a document."""

    id: str
    chat_id: str
    filename: str
    original_filename: str
    mime_type: str
    file_size: Optional[int] = None
    page_count: Optional[int] = None
    status: str
    error_message: Optional[str] = None
    created_at: str
    updated_at: str
    file_url: Optional[str] = None


class DocumentUploadResponse(BaseModel):
    """Response model for document upload."""

    success: bool
    document: Optional[DocumentResponse] = None
    error: Optional[str] = None


class DocumentListResponse(BaseModel):
    """Response model for listing documents."""

    documents: list[DocumentResponse]
    total: int


class DocumentChunkResponse(BaseModel):
    """Response model for a document chunk."""

    id: str
    chunk_index: int
    content: str
    page_number: Optional[int] = None


class DocumentChunksResponse(BaseModel):
    """Response model for document chunks."""

    document_id: str
    chunks: list[DocumentChunkResponse]
    total: int


def document_to_response(doc: Document) -> DocumentResponse:
    """Convert Document model to response."""
    # Construct file URL if it's stored
    file_url = None
    if doc.filename:
        file_url = f"/api/v1/documents/file/{doc.id}"

    return DocumentResponse(
        id=doc.id,
        chat_id=doc.chat_id,
        filename=doc.filename,
        original_filename=doc.original_filename,
        mime_type=doc.mime_type,
        file_size=doc.file_size,
        page_count=doc.page_count,
        status=doc.status,
        error_message=doc.error_message,
        created_at=doc.created_at.isoformat(),
        updated_at=doc.updated_at.isoformat(),
        file_url=file_url,
    )


@router.post("/documents/upload", response_model=DocumentUploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    chat_id: str = Form(...),
):
    """
    Upload and process a PDF document.

    The document will be associated with the specified chat and processed
    to extract text content for use in chat context.
    """
    logger.info(f"Document upload request received: chat_id={chat_id}, filename={file.filename}")

    # Validate file type
    # Check mime type first, then fallback to extension if mime type is generic
    file_extension = os.path.splitext(file.filename or "")[1].lower()
    allowed_extensions = [
        ".pdf", ".docx", ".pptx", ".xlsx", ".xls", ".ppt", ".doc",
        ".html", ".htm", ".md", ".txt", ".rtf", ".adoc", ".xml",
        ".png", ".jpg", ".jpeg", ".webp", ".gif", ".tiff", ".bmp",
        ".mp3", ".wav", ".ogg", ".m4a", ".mp4"
    ]
    
    if file.content_type not in ALLOWED_MIME_TYPES and file_extension not in allowed_extensions:
        logger.warning(f"Invalid file type: {file.content_type} ({file_extension})")
        return DocumentUploadResponse(
            success=False,
            error=f"Unsupported file type. Supported formats: PDF, MS Office, Markdown, Text, Image, Audio. Got: {file.content_type}",
        )

    # Read file content
    try:
        content = await file.read()
    except Exception as e:
        logger.error(f"Error reading uploaded file: {e}")
        return DocumentUploadResponse(
            success=False,
            error="Failed to read uploaded file",
        )

    # Validate file size
    file_size = len(content)
    if file_size > MAX_FILE_SIZE_BYTES:
        return DocumentUploadResponse(
            success=False,
            error=f"File too large. Maximum size is {MAX_FILE_SIZE_MB}MB",
        )

    if file_size == 0:
        return DocumentUploadResponse(
            success=False,
            error="File is empty",
        )

    # Generate document ID and sanitized filename
    document_id = str(uuid.uuid4())
    original_filename = file.filename or "document.pdf"
    # Sanitize filename for storage
    safe_filename = f"{document_id}.pdf"

    # Define storage path
    storage_dir = os.path.join("data", "storage", "documents")
    os.makedirs(storage_dir, exist_ok=True)
    file_path = os.path.join(storage_dir, safe_filename)

    # Save content to permanent storage
    try:
        with open(file_path, "wb") as f:
            f.write(content)
    except Exception as e:
        logger.error(f"Error saving document to storage: {e}")
        return DocumentUploadResponse(
            success=False,
            error="Failed to save document to storage",
        )

    # Create document record
    document_repo = DocumentRepository()
    doc = Document(
        id=document_id,
        chat_id=chat_id,
        filename=safe_filename,
        original_filename=original_filename,
        mime_type=file.content_type or "application/pdf",
        file_size=file_size,
        file_path=file_path,
        status="pending",
    )

    try:
        document_repo.create(doc)
    except Exception as e:
        logger.error(f"Error creating document record: {e}")
        return DocumentUploadResponse(
            success=False,
            error="Failed to create document record",
        )

    # Identify documents that can be processed by Docling
    extractable_types = [
        "application/pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "application/vnd.ms-excel",
        "application/vnd.ms-powerpoint",
        "application/msword",
        "text/html",
        "text/markdown",
        "text/x-markdown",
        "text/plain",
        "text/asciidoc",
        "application/rtf",
        "application/xml",
        "text/xml",
    ]

    # Extension-based check for robust detection
    extractable_extensions = [
        ".pdf", ".docx", ".pptx", ".xlsx", ".xls", ".ppt", ".doc",
        ".html", ".htm", ".md", ".txt", ".rtf", ".adoc", ".xml"
    ]
    file_extension = os.path.splitext(original_filename)[1].lower()
    is_extractable = (
        file.content_type in extractable_types or 
        file_extension in extractable_extensions
    )

    try:
        if file_extension == ".txt":
            # Handle .txt files separately as raw text to bypass Docling
            try:
                text_content = content.decode("utf-8")
            except UnicodeDecodeError:
                # Fallback to Latin-1 if UTF-8 fails
                text_content = content.decode("latin-1", errors="replace")
            
            result = document_service.process_raw_text(
                text=text_content,
                document_id=document_id,
                original_filename=original_filename,
            )
            success = result.success
            error_message = result.error_message
        elif is_extractable:
            # Use original extension for better format detection by Docling
            suffix = file_extension or ".pdf"
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
                temp_file.write(content)
                temp_path = temp_file.name

            try:
                result = document_service.process_document(
                    file_path=temp_path,
                    document_id=document_id,
                    original_filename=original_filename,
                )
                success = result.success
                error_message = result.error_message
            finally:
                # Clean up temp file
                try:
                    os.unlink(temp_path)
                except Exception:
                    pass
        else:
            # For images and audio, we don't extract text yet, just enable preview
            logger.info(f"Skipping text extraction for {file.content_type}, marking as completed")
            document_repo.update_status(document_id, "completed")
            success = True
            error_message = None


        if success:
            # Fetch updated document
            updated_doc = document_repo.get_by_id(document_id)
            if updated_doc:
                return DocumentUploadResponse(
                    success=True,
                    document=document_to_response(updated_doc),
                )
            else:
                return DocumentUploadResponse(
                    success=True,
                    document=document_to_response(doc),
                )
        else:
            # Fetch document with error status
            error_doc = document_repo.get_by_id(document_id)
            return DocumentUploadResponse(
                success=False,
                document=document_to_response(error_doc) if error_doc else None,
                error=error_message,
            )

    except Exception as e:
        logger.error(f"Error processing document: {e}")
        # Clean up temp file if it exists
        try:
            if 'temp_path' in locals():
                os.unlink(temp_path)
        except Exception:
            pass

        # Update document status to error
        document_repo.update_status(
            document_id,
            "error",
            error_message=str(e)[:500],
        )

        return DocumentUploadResponse(
            success=False,
            error=f"Failed to process document: {str(e)}",
        )


@router.get("/documents/{document_id}", response_model=DocumentResponse)
async def get_document(document_id: str):
    """Get document metadata by ID."""
    doc = document_service.get_document(document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return document_to_response(doc)


@router.delete("/documents/{document_id}")
async def delete_document(document_id: str):
    """Delete a document and its chunks."""
    doc = document_service.get_document(document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    success = document_service.delete_document(document_id)
    if success:
        return {"success": True, "message": "Document deleted"}
    else:
        raise HTTPException(status_code=500, detail="Failed to delete document")


@router.get("/chats/{chat_id}/documents", response_model=DocumentListResponse)
async def get_chat_documents(chat_id: str):
    """Get all documents for a chat."""
    documents = document_service.get_documents_for_chat(chat_id)
    return DocumentListResponse(
        documents=[document_to_response(doc) for doc in documents],
        total=len(documents),
    )


@router.get(
    "/documents/{document_id}/chunks",
    response_model=DocumentChunksResponse,
)
async def get_document_chunks(
    document_id: str,
    limit: Optional[int] = None,
):
    """Get extracted text chunks for a document."""
    doc = document_service.get_document(document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    chunks = document_service.get_document_chunks(document_id, limit=limit)

    return DocumentChunksResponse(
        document_id=document_id,
        chunks=[
            DocumentChunkResponse(
                id=chunk.id,
                chunk_index=chunk.chunk_index,
                content=chunk.content,
                page_number=chunk.page_number,
            )
            for chunk in chunks
        ],
        total=len(chunks),
    )

@router.get("/documents/file/{document_id}")
async def get_document_file(document_id: str):
    """Get the original document file."""
    doc = document_service.get_document(document_id)
    if not doc or not doc.file_path or not os.path.exists(doc.file_path):
        raise HTTPException(status_code=404, detail="Document file not found")
    
    return FileResponse(
        path=doc.file_path,
        filename=doc.original_filename,
        media_type=doc.mime_type,
        content_disposition_type="inline"
    )
