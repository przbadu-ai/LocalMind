"""Database migration system similar to Rails migrations.

This module provides a versioned migration system that:
1. Tracks which migrations have been run in a schema_migrations table
2. Runs pending migrations in order by version number
3. Supports both up (apply) migrations
4. Each migration is a Python file with a version timestamp and description

Usage:
    from database.migrator import run_migrations
    run_migrations(connection)

Migration files should be named like:
    20231215120000_create_chats_table.py
    20231216100000_add_is_pinned_to_chats.py

Each migration file should contain:
    VERSION = "20231215120000"
    DESCRIPTION = "Create chats table"

    def up(conn: sqlite3.Connection) -> None:
        conn.execute('''CREATE TABLE ...''')
"""

import importlib
import sqlite3
from pathlib import Path
from typing import List, Tuple


MIGRATIONS_DIR = Path(__file__).parent / "migrations"


def ensure_schema_migrations_table(conn: sqlite3.Connection) -> None:
    """Create the schema_migrations table if it doesn't exist."""
    conn.execute("""
        CREATE TABLE IF NOT EXISTS schema_migrations (
            version TEXT PRIMARY KEY,
            description TEXT,
            applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()


def get_applied_migrations(conn: sqlite3.Connection) -> set[str]:
    """Get the set of already applied migration versions."""
    cursor = conn.execute("SELECT version FROM schema_migrations ORDER BY version")
    return {row[0] for row in cursor.fetchall()}


def get_pending_migrations(conn: sqlite3.Connection) -> List[Tuple[str, str, Path]]:
    """Get list of pending migrations as (version, description, path) tuples."""
    applied = get_applied_migrations(conn)
    pending = []

    if not MIGRATIONS_DIR.exists():
        return pending

    for migration_file in sorted(MIGRATIONS_DIR.glob("*.py")):
        if migration_file.name == "__init__.py":
            continue

        # Extract version from filename (e.g., 20231215120000_create_chats.py)
        version = migration_file.stem.split("_")[0]

        if version not in applied:
            # Import the module to get description
            module_name = f"database.migrations.{migration_file.stem}"
            try:
                module = importlib.import_module(module_name)
                description = getattr(module, "DESCRIPTION", migration_file.stem)
                pending.append((version, description, migration_file))
            except ImportError as e:
                print(f"Warning: Could not import migration {migration_file.name}: {e}")

    return sorted(pending, key=lambda x: x[0])


def run_migration(conn: sqlite3.Connection, version: str, description: str, path: Path) -> None:
    """Run a single migration."""
    module_name = f"database.migrations.{path.stem}"
    module = importlib.import_module(module_name)

    if not hasattr(module, "up"):
        raise ValueError(f"Migration {path.name} does not have an 'up' function")

    print(f"  Running migration {version}: {description}")

    # Run the migration
    module.up(conn)

    # Record that migration was applied
    conn.execute(
        "INSERT INTO schema_migrations (version, description) VALUES (?, ?)",
        (version, description)
    )
    conn.commit()


def run_migrations(conn: sqlite3.Connection) -> int:
    """Run all pending migrations.

    Returns:
        Number of migrations that were run.
    """
    ensure_schema_migrations_table(conn)

    pending = get_pending_migrations(conn)

    if not pending:
        return 0

    print(f"Running {len(pending)} pending migration(s)...")

    for version, description, path in pending:
        run_migration(conn, version, description, path)

    print(f"Completed {len(pending)} migration(s).")
    return len(pending)


def get_migration_status(conn: sqlite3.Connection) -> dict:
    """Get the current migration status."""
    ensure_schema_migrations_table(conn)

    applied = get_applied_migrations(conn)
    pending = get_pending_migrations(conn)

    return {
        "applied_count": len(applied),
        "pending_count": len(pending),
        "applied_versions": sorted(applied),
        "pending_versions": [v for v, _, _ in pending],
    }
