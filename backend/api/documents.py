"""
Document management API endpoints.

This module handles all document-related operations including:
- Document upload and storage
- Processing and chunking
- Vector embedding generation
- Document listing and deletion
"""

from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import List
from models.schemas import DocumentResponse
from services import DocumentService, VectorService
from config import settings
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

# Initialize services
document_service = DocumentService()
vector_service = VectorService()


@router.post("/upload", response_model=DocumentResponse)
async def upload_document(file: UploadFile = File(...)):
    """
    Upload and process a new document.

    This endpoint:
    1. Validates file size and type
    2. Saves the document to storage
    3. Extracts text and creates chunks
    4. Generates embeddings and stores in vector DB
    5. Returns document metadata

    Args:
        file: Uploaded file (multipart/form-data)

    Supported formats:
        - PDF (.pdf)
        - Word Documents (.docx)
        - Text files (.txt)
        - Markdown (.md)
        - PowerPoint (.pptx)
        - Images (.png, .jpg, .jpeg)

    Returns:
        DocumentResponse with:
        - Document ID (SHA256 hash)
        - Filename and type
        - File size
        - Number of chunks created
        - Upload timestamp

    Raises:
        HTTPException: 413 if file exceeds size limit
        HTTPException: 400 if file type unsupported or processing fails

    Example:
        ```python
        with open("document.pdf", "rb") as f:
            response = requests.post(
                "/api/v1/documents/upload",
                files={"file": ("document.pdf", f, "application/pdf")}
            )
        ```
    """
    try:
        # Validate file size
        file_content = await file.read()
        file_size_mb = len(file_content) / (1024 * 1024)

        if file_size_mb > settings.max_file_size_mb:
            raise HTTPException(
                status_code=413,
                detail=f"File size exceeds {settings.max_file_size_mb}MB limit"
            )

        # Save document
        document = await document_service.save_document(file_content, file.filename)

        # Process document and extract chunks
        processed_data = await document_service.process_document(document.id)

        # Add to vector store
        await vector_service.add_embeddings(
            processed_data["chunks"],
            document.id,
            document.filename
        )

        # Update chunks count
        document.chunks_count = len(processed_data["chunks"])

        return document

    except Exception as e:
        logger.error(f"Document upload failed: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/", response_model=List[DocumentResponse])
async def list_documents():
    """
    List all uploaded documents.

    Returns a list of all documents in the system with their metadata.
    Documents are sorted by upload date (newest first).

    Returns:
        List of DocumentResponse objects

    Raises:
        HTTPException: 500 if listing fails

    Example:
        ```python
        response = requests.get("/api/v1/documents/")
        documents = response.json()
        # [{"id": "abc123", "filename": "doc.pdf", ...}, ...]
        ```
    """
    try:
        return await document_service.list_documents()
    except Exception as e:
        logger.error(f"Failed to list documents: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(document_id: str):
    """
    Get details of a specific document.

    Retrieves metadata for a single document by its ID.

    Args:
        document_id: Unique document identifier (SHA256 hash)

    Returns:
        DocumentResponse with document metadata

    Raises:
        HTTPException: 404 if document not found
        HTTPException: 500 if retrieval fails

    Example:
        ```python
        response = requests.get("/api/v1/documents/abc123def456")
        ```
    """
    documents = await document_service.list_documents()
    for doc in documents:
        if doc.id == document_id:
            return doc
    raise HTTPException(status_code=404, detail="Document not found")


@router.delete("/{document_id}")
async def delete_document(document_id: str):
    """
    Delete a document and its embeddings.

    Permanently removes:
    - Document file from storage
    - All vector embeddings from database
    - Associated metadata

    Args:
        document_id: Document ID to delete

    Returns:
        Success message

    Raises:
        HTTPException: 404 if document not found
        HTTPException: 500 if deletion fails

    Warning:
        This operation is irreversible. All data associated
        with the document will be permanently deleted.

    Example:
        ```python
        response = requests.delete("/api/v1/documents/abc123def456")
        # Returns: {"message": "Document deleted successfully"}
        ```
    """
    try:
        # Delete from vector store
        await vector_service.delete_document(document_id)

        # Delete from file system
        success = await document_service.delete_document(document_id)

        if success:
            return {"message": "Document deleted successfully"}
        else:
            raise HTTPException(status_code=404, detail="Document not found")

    except Exception as e:
        logger.error(f"Failed to delete document: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{document_id}/reprocess")
async def reprocess_document(document_id: str):
    """
    Reprocess a document and update embeddings.

    Useful when:
    - Changing chunk size or overlap settings
    - Updating to a new embedding model
    - Fixing corrupted embeddings
    - After document processing improvements

    This endpoint:
    1. Deletes existing embeddings
    2. Re-extracts text from the document
    3. Creates new chunks with current settings
    4. Generates fresh embeddings

    Args:
        document_id: Document ID to reprocess

    Returns:
        Dict containing:
        - message: Success confirmation
        - chunks_count: Number of chunks created

    Raises:
        HTTPException: 404 if document not found
        HTTPException: 500 if reprocessing fails

    Example:
        ```python
        response = requests.post("/api/v1/documents/abc123/reprocess")
        # Returns: {"message": "Document reprocessed successfully", "chunks_count": 42}
        ```
    """
    try:
        # Delete existing embeddings
        await vector_service.delete_document(document_id)

        # Reprocess document
        processed_data = await document_service.process_document(document_id)

        # Get document info
        documents = await document_service.list_documents()
        document = None
        for doc in documents:
            if doc.id == document_id:
                document = doc
                break

        if not document:
            raise HTTPException(status_code=404, detail="Document not found")

        # Add new embeddings
        await vector_service.add_embeddings(
            processed_data["chunks"],
            document_id,
            document.filename
        )

        return {
            "message": "Document reprocessed successfully",
            "chunks_count": len(processed_data["chunks"])
        }

    except Exception as e:
        logger.error(f"Failed to reprocess document: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))