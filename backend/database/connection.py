"""SQLite database connection and initialization."""

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Generator

from config import settings


def get_db_path() -> Path:
    """Get the database file path, creating parent directories if needed."""
    db_path = settings.database_full_path
    db_path.parent.mkdir(parents=True, exist_ok=True)
    return db_path


def init_db() -> None:
    """Initialize the database and run pending migrations."""
    from database.migrator import run_migrations

    db_path = get_db_path()
    conn = sqlite3.connect(str(db_path))

    try:
        # Run all pending migrations
        migrations_run = run_migrations(conn)
        if migrations_run > 0:
            print(f"Database initialized with {migrations_run} migration(s)")
    finally:
        conn.close()


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
