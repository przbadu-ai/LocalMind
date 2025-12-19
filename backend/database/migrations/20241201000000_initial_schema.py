"""Initial database schema migration.

This creates the base tables that existed before the migration system.
"""

import sqlite3

VERSION = "20241201000000"
DESCRIPTION = "Create initial schema (chats, messages, tags, transcripts, configurations, mcp_servers)"


def up(conn: sqlite3.Connection) -> None:
    """Apply the migration."""
    conn.executescript("""
        -- Chats table
        CREATE TABLE IF NOT EXISTS chats (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL DEFAULT 'New Chat',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_archived INTEGER DEFAULT 0
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
    """)
