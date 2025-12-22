"""Add documents and document_chunks tables for PDF document support."""

import sqlite3

VERSION = "20241223000000"
DESCRIPTION = "Add documents and document_chunks tables for PDF support"


def up(conn: sqlite3.Connection) -> None:
    """Apply the migration."""
    # Create documents table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS documents (
            id TEXT PRIMARY KEY,
            chat_id TEXT NOT NULL,
            filename TEXT NOT NULL,
            original_filename TEXT NOT NULL,
            mime_type TEXT DEFAULT 'application/pdf',
            file_size INTEGER,
            page_count INTEGER,
            status TEXT DEFAULT 'pending' CHECK(status IN ('pending', 'processing', 'completed', 'error')),
            error_message TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (chat_id) REFERENCES chats(id) ON DELETE CASCADE
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_documents_chat_id ON documents(chat_id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_documents_status ON documents(status)")

    # Create document_chunks table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS document_chunks (
            id TEXT PRIMARY KEY,
            document_id TEXT NOT NULL,
            chunk_index INTEGER NOT NULL,
            content TEXT NOT NULL,
            page_number INTEGER,
            char_start INTEGER,
            char_end INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_document_chunks_document_id ON document_chunks(document_id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_document_chunks_order ON document_chunks(document_id, chunk_index)")
