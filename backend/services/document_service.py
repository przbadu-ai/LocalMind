"""
Document management service for file handling and processing.

This module handles document lifecycle operations including:
- File upload and storage
- Document type detection
- Text extraction and chunking
- Metadata management
"""

import os
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
import aiofiles
from models.schemas import DocumentType, DocumentResponse
from core.exceptions import DocumentProcessingError
from config.app_settings import config
import logging

logger = logging.getLogger(__name__)


class DocumentService:
    """
    Service for handling document uploads and processing.

    Manages the complete document lifecycle from upload to deletion,
    including file storage, type detection, and metadata tracking.

    Attributes:
        uploads_dir: Directory for storing uploaded documents
        supported_extensions: Map of file extensions to DocumentType
    """

    def __init__(self):
        self.uploads_dir = config.uploads_dir
        self.supported_extensions = {
            ".pdf": DocumentType.PDF,
            ".docx": DocumentType.DOCX,
            ".txt": DocumentType.TXT,
            ".md": DocumentType.MD,
            ".pptx": DocumentType.PPTX,
            ".png": DocumentType.IMAGE,
            ".jpg": DocumentType.IMAGE,
            ".jpeg": DocumentType.IMAGE,
        }

    async def save_document(self, file_content: bytes, filename: str) -> DocumentResponse:
        """Save uploaded document to disk."""
        try:
            # Generate document ID
            doc_id = self._generate_document_id(file_content)

            # Determine document type
            file_ext = Path(filename).suffix.lower()
            if file_ext not in self.supported_extensions:
                raise DocumentProcessingError(f"Unsupported file type: {file_ext}")

            doc_type = self.supported_extensions[file_ext]

            # Save file
            file_path = self.uploads_dir / f"{doc_id}{file_ext}"
            async with aiofiles.open(file_path, 'wb') as f:
                await f.write(file_content)

            # Create response
            return DocumentResponse(
                id=doc_id,
                filename=filename,
                document_type=doc_type,
                file_size=len(file_content),
                chunks_count=0,  # Will be updated after processing
                created_at=datetime.utcnow(),
                metadata={"path": str(file_path)}
            )
        except Exception as e:
            logger.error(f"Error saving document: {str(e)}")
            raise DocumentProcessingError(f"Failed to save document: {str(e)}")

    async def process_document(self, doc_id: str) -> Dict[str, Any]:
        """Process document and extract text with position information."""
        # This will be implemented with PyMuPDF
        # For now, return mock data
        return {
            "chunks": [
                {
                    "text": "This is a sample chunk from the document",
                    "page": 1,
                    "bbox": {"x0": 100, "y0": 200, "x1": 300, "y1": 250},
                    "chunk_id": f"{doc_id}_chunk_1"
                }
            ],
            "total_pages": 1,
            "metadata": {
                "processed_at": datetime.utcnow().isoformat()
            }
        }

    async def delete_document(self, doc_id: str) -> bool:
        """Delete a document and its associated data."""
        try:
            # Find and delete the file
            for file_path in self.uploads_dir.glob(f"{doc_id}*"):
                file_path.unlink()
                return True
            return False
        except Exception as e:
            logger.error(f"Error deleting document: {str(e)}")
            raise DocumentProcessingError(f"Failed to delete document: {str(e)}")

    async def list_documents(self) -> List[DocumentResponse]:
        """List all uploaded documents."""
        documents = []
        for file_path in self.uploads_dir.glob("*"):
            if file_path.is_file():
                doc_id = file_path.stem
                file_ext = file_path.suffix.lower()
                if file_ext in self.supported_extensions:
                    documents.append(DocumentResponse(
                        id=doc_id,
                        filename=file_path.name,
                        document_type=self.supported_extensions[file_ext],
                        file_size=file_path.stat().st_size,
                        chunks_count=0,
                        created_at=datetime.fromtimestamp(file_path.stat().st_ctime),
                        metadata={"path": str(file_path)}
                    ))
        return documents

    def _generate_document_id(self, content: bytes) -> str:
        """Generate a unique document ID based on content hash."""
        return hashlib.sha256(content).hexdigest()[:16]