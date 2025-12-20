"""Add tool_calls column to messages table for MCP tool call persistence."""

import sqlite3

VERSION = "20241220000000"
DESCRIPTION = "Add tool_calls column to messages table"


def up(conn: sqlite3.Connection) -> None:
    """Apply the migration."""
    # Check existing columns
    cursor = conn.execute("PRAGMA table_info(messages)")
    columns = [row[1] for row in cursor.fetchall()]

    if "tool_calls" not in columns:
        # tool_calls will be stored as JSON text
        conn.execute("ALTER TABLE messages ADD COLUMN tool_calls TEXT")
