"""Create llm_providers table for multi-provider LLM support."""

import json
import sqlite3
import uuid

VERSION = "20241215000000"
DESCRIPTION = "Create llm_providers table"


def up(conn: sqlite3.Connection) -> None:
    """Apply the migration."""
    # Create the llm_providers table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS llm_providers (
            id TEXT PRIMARY KEY,
            name TEXT UNIQUE NOT NULL,
            base_url TEXT NOT NULL,
            api_key TEXT,
            model TEXT,
            is_default INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Migrate existing LLM config from configurations table if it exists
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
