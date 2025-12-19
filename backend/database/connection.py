"""SQLite database connection and initialization."""

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Generator

from config import settings

# SQL schema for all tables
SCHEMA = """
-- Chats table
CREATE TABLE IF NOT EXISTS chats (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL DEFAULT 'New Chat',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_archived INTEGER DEFAULT 0,
    is_pinned INTEGER DEFAULT 0
);

-- Chat tags
CREATE TABLE IF NOT EXISTS chat_tags (
    id TEXT PRIMARY KEY,
    name TEXT UNIQUE NOT NULL,
    color TEXT DEFAULT '#6B7280'
);

-- Chat tag assignments (many-to-many)
CREATE TABLE IF NOT EXISTS chat_tag_assignments (
    chat_id TEXT NOT NULL,
    tag_id TEXT NOT NULL,
    PRIMARY KEY (chat_id, tag_id),
    FOREIGN KEY (chat_id) REFERENCES chats(id) ON DELETE CASCADE,
    FOREIGN KEY (tag_id) REFERENCES chat_tags(id) ON DELETE CASCADE
);

-- Messages table
CREATE TABLE IF NOT EXISTS messages (
    id TEXT PRIMARY KEY,
    chat_id TEXT NOT NULL,
    role TEXT NOT NULL CHECK(role IN ('user', 'assistant', 'system')),
    content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    artifact_type TEXT,
    artifact_data JSON,
    FOREIGN KEY (chat_id) REFERENCES chats(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_messages_chat_id ON messages(chat_id);
CREATE INDEX IF NOT EXISTS idx_messages_created_at ON messages(created_at);

-- Transcripts table (YouTube video transcripts)
CREATE TABLE IF NOT EXISTS transcripts (
    id TEXT PRIMARY KEY,
    video_id TEXT UNIQUE NOT NULL,
    video_url TEXT NOT NULL,
    video_title TEXT,
    language_code TEXT DEFAULT 'en',
    is_generated INTEGER DEFAULT 0,
    raw_transcript JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_transcripts_video_id ON transcripts(video_id);

-- Configurations table
CREATE TABLE IF NOT EXISTS configurations (
    key TEXT PRIMARY KEY,
    value JSON NOT NULL,
    category TEXT DEFAULT 'general'
);

-- MCP Servers table
CREATE TABLE IF NOT EXISTS mcp_servers (
    id TEXT PRIMARY KEY,
    name TEXT UNIQUE NOT NULL,
    transport_type TEXT NOT NULL CHECK(transport_type IN ('stdio', 'sse')),
    command TEXT,
    args JSON,
    url TEXT,
    env JSON,
    enabled INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- LLM Providers table
CREATE TABLE IF NOT EXISTS llm_providers (
    id TEXT PRIMARY KEY,
    name TEXT UNIQUE NOT NULL,
    base_url TEXT NOT NULL,
    api_key TEXT,
    model TEXT,
    is_default INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""


def get_db_path() -> Path:
    """Get the database file path, creating parent directories if needed."""
    db_path = settings.database_full_path
    db_path.parent.mkdir(parents=True, exist_ok=True)
    return db_path


def init_db() -> None:
    """Initialize the database with schema."""
    db_path = get_db_path()
    conn = sqlite3.connect(str(db_path))
    conn.executescript(SCHEMA)
    
    # Run migrations
    _migrate_db(conn)
    
    conn.commit()
    conn.close()


def _migrate_db(conn: sqlite3.Connection) -> None:
    """Run database migrations."""
    import json
    import uuid

    # Check if is_pinned column exists in chats table
    cursor = conn.execute("PRAGMA table_info(chats)")
    columns = [row[1] for row in cursor.fetchall()]

    if "is_pinned" not in columns:
        conn.execute("ALTER TABLE chats ADD COLUMN is_pinned INTEGER DEFAULT 0")

    # Migrate existing LLM config from configurations table to llm_providers
    # Check if llm_providers table has any data
    cursor = conn.execute("SELECT COUNT(*) FROM llm_providers")
    provider_count = cursor.fetchone()[0]

    if provider_count == 0:
        # Check if there's existing LLM config in configurations table
        cursor = conn.execute(
            "SELECT value FROM configurations WHERE key = 'llm'"
        )
        row = cursor.fetchone()

        if row:
            try:
                llm_config = json.loads(row[0])
                provider_name = llm_config.get("provider", "ollama")
                base_url = llm_config.get("base_url", "http://localhost:11434/v1")
                api_key = llm_config.get("api_key", "")
                model = llm_config.get("model", "")

                # Insert into llm_providers as default
                conn.execute(
                    """
                    INSERT INTO llm_providers (id, name, base_url, api_key, model, is_default)
                    VALUES (?, ?, ?, ?, ?, 1)
                    """,
                    (str(uuid.uuid4()), provider_name, base_url, api_key, model),
                )

                # Delete the legacy configuration entry
                conn.execute("DELETE FROM configurations WHERE key = 'llm'")
            except (json.JSONDecodeError, KeyError):
                pass


@contextmanager
def get_db() -> Generator[sqlite3.Connection, None, None]:
    """Get a database connection as a context manager."""
    db_path = get_db_path()
    conn = sqlite3.connect(str(db_path), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
    finally:
        conn.close()
