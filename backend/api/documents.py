from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from typing import List
from models.schemas import DocumentResponse, DocumentUpload
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
    """Upload a new document for processing."""
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
    """List all uploaded documents."""
    try:
        return await document_service.list_documents()
    except Exception as e:
        logger.error(f"Failed to list documents: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(document_id: str):
    """Get details of a specific document."""
    documents = await document_service.list_documents()
    for doc in documents:
        if doc.id == document_id:
            return doc
    raise HTTPException(status_code=404, detail="Document not found")


@router.delete("/{document_id}")
async def delete_document(document_id: str):
    """Delete a document and its embeddings."""
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
    """Reprocess a document and update embeddings."""
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