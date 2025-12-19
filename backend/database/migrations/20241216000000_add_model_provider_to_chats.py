"""Add model and provider columns to chats table for per-chat model selection."""

import sqlite3

VERSION = "20241216000000"
DESCRIPTION = "Add model and provider columns to chats table"


def up(conn: sqlite3.Connection) -> None:
    """Apply the migration."""
    # Check existing columns
    cursor = conn.execute("PRAGMA table_info(chats)")
    columns = [row[1] for row in cursor.fetchall()]

    if "model" not in columns:
        conn.execute("ALTER TABLE chats ADD COLUMN model TEXT")

    if "provider" not in columns:
        conn.execute("ALTER TABLE chats ADD COLUMN provider TEXT")
