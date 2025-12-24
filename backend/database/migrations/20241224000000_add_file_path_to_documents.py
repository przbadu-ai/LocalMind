"""Add file_path column to documents table."""

import sqlite3

VERSION = "20241224000000"
DESCRIPTION = "Add file_path column to documents table"


def up(conn: sqlite3.Connection) -> None:
    """Apply the migration."""
    # Add file_path column to documents table
    try:
        conn.execute("ALTER TABLE documents ADD COLUMN file_path TEXT")
    except sqlite3.OperationalError:
        # Column may already exist
        pass


def down(conn: sqlite3.Connection) -> None:
    """Revert the migration."""
    # SQLite does not support dropping columns easily (requires recreating the table)
    # For this simple migration, we'll leave it
    pass
