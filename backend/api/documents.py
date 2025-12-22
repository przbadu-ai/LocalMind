"""Document upload and management API endpoints."""

import logging
import os
import tempfile
import uuid
from typing import Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
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
ALLOWED_MIME_TYPES = ["application/pdf"]


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
    if file.content_type not in ALLOWED_MIME_TYPES:
        logger.warning(f"Invalid file type: {file.content_type}")
        return DocumentUploadResponse(
            success=False,
            error=f"Invalid file type. Only PDF files are supported. Got: {file.content_type}",
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

    # Create document record
    document_repo = DocumentRepository()
    doc = Document(
        id=document_id,
        chat_id=chat_id,
        filename=safe_filename,
        original_filename=original_filename,
        mime_type=file.content_type or "application/pdf",
        file_size=file_size,
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

    # Save to temp file and process
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
            temp_file.write(content)
            temp_path = temp_file.name

        # Process the document (extract text, create chunks)
        result = document_service.process_pdf(
            file_path=temp_path,
            document_id=document_id,
            original_filename=original_filename,
        )

        # Clean up temp file
        try:
            os.unlink(temp_path)
        except Exception:
            pass

        logger.info(f"Document processing result: success={result.success}, chunks={result.chunk_count}")

        if result.success:
            # Fetch updated document
            updated_doc = document_repo.get_by_id(document_id)
            logger.info(f"Fetched updated document: {updated_doc.id if updated_doc else 'None'}, status={updated_doc.status if updated_doc else 'N/A'}")
            if updated_doc:
                response = DocumentUploadResponse(
                    success=True,
                    document=document_to_response(updated_doc),
                )
                logger.info(f"Returning successful response for document {document_id}")
                return response
            else:
                response = DocumentUploadResponse(
                    success=True,
                    document=document_to_response(doc),
                )
                logger.info(f"Returning response with original doc for document {document_id}")
                return response
        else:
            # Fetch document with error status
            error_doc = document_repo.get_by_id(document_id)
            logger.error(f"Document processing failed: {result.error_message}")
            return DocumentUploadResponse(
                success=False,
                document=document_to_response(error_doc) if error_doc else None,
                error=result.error_message,
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
