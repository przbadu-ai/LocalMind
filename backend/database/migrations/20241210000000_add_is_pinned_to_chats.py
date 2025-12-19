"""Add is_pinned column to chats table."""

import sqlite3

VERSION = "20241210000000"
DESCRIPTION = "Add is_pinned column to chats table"


def up(conn: sqlite3.Connection) -> None:
    """Apply the migration."""
    # Check if column already exists (for existing databases)
    cursor = conn.execute("PRAGMA table_info(chats)")
    columns = [row[1] for row in cursor.fetchall()]

    if "is_pinned" not in columns:
        conn.execute("ALTER TABLE chats ADD COLUMN is_pinned INTEGER DEFAULT 0")
