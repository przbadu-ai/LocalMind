"""Repository for document operations."""

from datetime import datetime
from typing import Optional

from database.connection import get_db
from database.models import Document, DocumentChunk


class DocumentRepository:
    """Repository for managing uploaded documents."""

    def create(self, document: Document) -> Document:
        """Create a new document record."""
        with get_db() as conn:
            conn.execute(
                """
                INSERT INTO documents (id, chat_id, filename, original_filename, mime_type, file_size, page_count, file_path, status, error_message, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    document.id,
                    document.chat_id,
                    document.filename,
                    document.original_filename,
                    document.mime_type,
                    document.file_size,
                    document.page_count,
                    document.file_path,
                    document.status,
                    document.error_message,
                    document.created_at.isoformat(),
                    document.updated_at.isoformat(),
                ),
            )
            conn.commit()
        return document

    def get_by_id(self, document_id: str) -> Optional[Document]:
        """Get a document by ID."""
        with get_db() as conn:
            row = conn.execute(
                "SELECT * FROM documents WHERE id = ?",
                (document_id,),
            ).fetchone()

            if not row:
                return None

            return self._row_to_document(row)

    def get_by_chat_id(self, chat_id: str) -> list[Document]:
        """Get all documents for a chat."""
        with get_db() as conn:
            rows = conn.execute(
                """
                SELECT * FROM documents
                WHERE chat_id = ?
                ORDER BY created_at DESC
                """,
                (chat_id,),
            ).fetchall()
            return [self._row_to_document(row) for row in rows]

    def get_completed_by_chat_id(self, chat_id: str) -> list[Document]:
        """Get all completed (processed) documents for a chat."""
        with get_db() as conn:
            rows = conn.execute(
                """
                SELECT * FROM documents
                WHERE chat_id = ? AND status = 'completed'
                ORDER BY created_at DESC
                """,
                (chat_id,),
            ).fetchall()
            return [self._row_to_document(row) for row in rows]

    def update_status(
        self,
        document_id: str,
        status: str,
        error_message: Optional[str] = None,
        page_count: Optional[int] = None,
    ) -> bool:
        """Update document status."""
        with get_db() as conn:
            if page_count is not None:
                conn.execute(
                    """
                    UPDATE documents
                    SET status = ?, error_message = ?, page_count = ?, updated_at = ?
                    WHERE id = ?
                    """,
                    (status, error_message, page_count, datetime.utcnow().isoformat(), document_id),
                )
            else:
                conn.execute(
                    """
                    UPDATE documents
                    SET status = ?, error_message = ?, updated_at = ?
                    WHERE id = ?
                    """,
                    (status, error_message, datetime.utcnow().isoformat(), document_id),
                )
            conn.commit()
            return True

    def delete(self, document_id: str) -> bool:
        """Delete a document by ID (chunks cascade delete)."""
        with get_db() as conn:
            cursor = conn.execute(
                "DELETE FROM documents WHERE id = ?",
                (document_id,),
            )
            conn.commit()
            return cursor.rowcount > 0

    def _row_to_document(self, row) -> Document:
        """Convert a database row to a Document model."""
        return Document(
            id=row["id"],
            chat_id=row["chat_id"],
            filename=row["filename"],
            original_filename=row["original_filename"],
            mime_type=row["mime_type"],
            file_size=row["file_size"],
            page_count=row["page_count"],
            file_path=row["file_path"] if "file_path" in row.keys() else None,
            status=row["status"],
            error_message=row["error_message"],
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
        )


class DocumentChunkRepository:
    """Repository for managing document chunks."""

    def create_many(self, chunks: list[DocumentChunk]) -> list[DocumentChunk]:
        """Create multiple chunks at once."""
        if not chunks:
            return []

        with get_db() as conn:
            conn.executemany(
                """
                INSERT INTO document_chunks (id, document_id, chunk_index, content, page_number, char_start, char_end, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        chunk.id,
                        chunk.document_id,
                        chunk.chunk_index,
                        chunk.content,
                        chunk.page_number,
                        chunk.char_start,
                        chunk.char_end,
                        chunk.created_at.isoformat(),
                    )
                    for chunk in chunks
                ],
            )
            conn.commit()
        return chunks

    def get_by_document_id(
        self, document_id: str, limit: Optional[int] = None
    ) -> list[DocumentChunk]:
        """Get all chunks for a document, ordered by chunk_index."""
        with get_db() as conn:
            if limit:
                rows = conn.execute(
                    """
                    SELECT * FROM document_chunks
                    WHERE document_id = ?
                    ORDER BY chunk_index ASC
                    LIMIT ?
                    """,
                    (document_id, limit),
                ).fetchall()
            else:
                rows = conn.execute(
                    """
                    SELECT * FROM document_chunks
                    WHERE document_id = ?
                    ORDER BY chunk_index ASC
                    """,
                    (document_id,),
                ).fetchall()
            return [self._row_to_chunk(row) for row in rows]

    def delete_by_document_id(self, document_id: str) -> int:
        """Delete all chunks for a document. Returns count deleted."""
        with get_db() as conn:
            cursor = conn.execute(
                "DELETE FROM document_chunks WHERE document_id = ?",
                (document_id,),
            )
            conn.commit()
            return cursor.rowcount

    def _row_to_chunk(self, row) -> DocumentChunk:
        """Convert a database row to a DocumentChunk model."""
        return DocumentChunk(
            id=row["id"],
            document_id=row["document_id"],
            chunk_index=row["chunk_index"],
            content=row["content"],
            page_number=row["page_number"],
            char_start=row["char_start"],
            char_end=row["char_end"],
            created_at=datetime.fromisoformat(row["created_at"]),
        )
