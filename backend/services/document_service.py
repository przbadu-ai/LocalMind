"""Document processing service using Docling."""

import logging
import os
import tempfile
from typing import Optional

from pydantic import BaseModel

from database.models import Document, DocumentChunk
from database.repositories.document_repository import (
    DocumentChunkRepository,
    DocumentRepository,
)

logger = logging.getLogger(__name__)


class DocumentResult(BaseModel):
    """Result of a document processing attempt."""

    success: bool
    document_id: str
    filename: str
    page_count: Optional[int] = None
    chunk_count: int = 0
    error_type: Optional[str] = None
    error_message: Optional[str] = None


class DocumentService:
    """Service for processing and managing uploaded documents."""

    def __init__(self):
        self.document_repo = DocumentRepository()
        self.chunk_repo = DocumentChunkRepository()
        self.chunk_size = 2000  # Characters per chunk
        self.chunk_overlap = 200  # Overlap for context continuity

    def process_pdf(
        self,
        file_path: str,
        document_id: str,
        original_filename: str,
    ) -> DocumentResult:
        """
        Process a PDF file using Docling and create chunks.

        Args:
            file_path: Path to the PDF file
            document_id: ID of the document record
            original_filename: Original filename for display

        Returns:
            DocumentResult with success status and processing info
        """
        try:
            # Import docling here to avoid startup overhead if not used
            from docling.document_converter import DocumentConverter

            # Update status to processing
            self.document_repo.update_status(document_id, "processing")

            # Initialize converter and process document
            converter = DocumentConverter()
            result = converter.convert(file_path)

            # Get the document and extract text
            doc = result.document

            # Get page count if available
            page_count = None
            if hasattr(doc, 'pages') and doc.pages:
                page_count = len(doc.pages)

            # Export to markdown for clean text extraction
            logger.info(f"Exporting document {document_id} to markdown...")
            full_text = doc.export_to_markdown()
            logger.info(f"Exported text length: {len(full_text) if full_text else 0} chars")

            if not full_text or not full_text.strip():
                logger.warning(f"No text extracted from document {document_id}")
                self.document_repo.update_status(
                    document_id,
                    "error",
                    error_message="No text could be extracted from the document",
                )
                return DocumentResult(
                    success=False,
                    document_id=document_id,
                    filename=original_filename,
                    error_type="NoTextExtracted",
                    error_message="No text could be extracted from the document. It may be an image-only PDF or corrupted.",
                )

            # Create chunks from the extracted text
            logger.info(f"Creating chunks for document {document_id}...")
            chunks = self._create_chunks(full_text, document_id)
            logger.info(f"Created {len(chunks)} chunks")

            # Save chunks to database
            logger.info(f"Saving chunks to database...")
            self.chunk_repo.create_many(chunks)
            logger.info(f"Chunks saved successfully")

            # Update document status to completed
            logger.info(f"Updating document {document_id} status to completed...")
            self.document_repo.update_status(
                document_id,
                "completed",
                page_count=page_count,
            )
            logger.info(f"Document {document_id} processing complete!")

            return DocumentResult(
                success=True,
                document_id=document_id,
                filename=original_filename,
                page_count=page_count,
                chunk_count=len(chunks),
            )

        except ImportError as e:
            logger.error(f"Docling not installed: {e}")
            self.document_repo.update_status(
                document_id,
                "error",
                error_message="Document processing library not available",
            )
            return DocumentResult(
                success=False,
                document_id=document_id,
                filename=original_filename,
                error_type="DependencyError",
                error_message="Document processing library (docling) is not installed.",
            )
        except Exception as e:
            error_type = type(e).__name__
            error_message = str(e)
            logger.error(f"Error processing document {document_id}: {error_type} - {error_message}")

            self.document_repo.update_status(
                document_id,
                "error",
                error_message=error_message[:500],  # Truncate long errors
            )

            return DocumentResult(
                success=False,
                document_id=document_id,
                filename=original_filename,
                error_type=error_type,
                error_message=error_message,
            )

    def _create_chunks(
        self,
        text: str,
        document_id: str,
    ) -> list[DocumentChunk]:
        """
        Split text into overlapping chunks.

        Args:
            text: Full document text
            document_id: ID of the parent document

        Returns:
            List of DocumentChunk objects
        """
        chunks = []
        text_length = len(text)

        if text_length == 0:
            return chunks

        # If text is smaller than chunk size, return as single chunk
        if text_length <= self.chunk_size:
            chunks.append(
                DocumentChunk(
                    document_id=document_id,
                    chunk_index=0,
                    content=text.strip(),
                    char_start=0,
                    char_end=text_length,
                )
            )
            return chunks

        # Create overlapping chunks
        start = 0
        chunk_index = 0

        while start < text_length:
            end = min(start + self.chunk_size, text_length)

            # Try to end at a sentence boundary if possible
            if end < text_length:
                # Look for sentence endings within the last 200 chars
                search_start = max(end - 200, start)
                last_period = text.rfind('. ', search_start, end)
                last_newline = text.rfind('\n', search_start, end)

                # Use the latest sentence boundary found
                boundary = max(last_period, last_newline)
                if boundary > search_start:
                    end = boundary + 1

            chunk_text = text[start:end].strip()

            if chunk_text:  # Only add non-empty chunks
                chunks.append(
                    DocumentChunk(
                        document_id=document_id,
                        chunk_index=chunk_index,
                        content=chunk_text,
                        char_start=start,
                        char_end=end,
                    )
                )
                chunk_index += 1

            # Move start forward, accounting for overlap
            start = end - self.chunk_overlap
            if start >= text_length:
                break

            # Prevent infinite loop
            if start <= 0 and chunk_index > 0:
                break

        return chunks

    def get_document(self, document_id: str) -> Optional[Document]:
        """Get a document by ID."""
        return self.document_repo.get_by_id(document_id)

    def get_documents_for_chat(self, chat_id: str) -> list[Document]:
        """Get all documents for a chat."""
        return self.document_repo.get_by_chat_id(chat_id)

    def get_completed_documents_for_chat(self, chat_id: str) -> list[Document]:
        """Get all completed documents for a chat."""
        return self.document_repo.get_completed_by_chat_id(chat_id)

    def get_document_chunks(
        self,
        document_id: str,
        limit: Optional[int] = None,
    ) -> list[DocumentChunk]:
        """Get chunks for a document."""
        return self.chunk_repo.get_by_document_id(document_id, limit=limit)

    def delete_document(self, document_id: str) -> bool:
        """Delete a document and its chunks."""
        return self.document_repo.delete(document_id)

    def build_context_from_documents(
        self,
        documents: list[Document],
        max_chars: int = 8000,
        max_chunks_per_doc: int = 10,
    ) -> str:
        """
        Build context string from multiple documents for LLM injection.

        Args:
            documents: List of completed documents
            max_chars: Maximum total characters to include
            max_chunks_per_doc: Maximum chunks to include per document

        Returns:
            Formatted context string
        """
        if not documents:
            return ""

        context_parts = []
        total_chars = 0

        for doc in documents:
            if doc.status != "completed":
                continue

            chunks = self.chunk_repo.get_by_document_id(
                doc.id, limit=max_chunks_per_doc
            )

            if not chunks:
                continue

            doc_text = "\n\n".join(chunk.content for chunk in chunks)

            # Check if adding this would exceed limit
            remaining = max_chars - total_chars
            if remaining <= 0:
                break

            if len(doc_text) > remaining:
                doc_text = doc_text[:remaining] + "... [truncated]"

            context_parts.append(
                f"--- Document: {doc.original_filename} ---\n{doc_text}"
            )
            total_chars += len(doc_text)

        return "\n\n".join(context_parts)


# Global document service instance
document_service = DocumentService()
