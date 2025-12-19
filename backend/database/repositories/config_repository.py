"""Repository for configuration and MCP server operations."""

import json
from datetime import datetime
from typing import Any, Optional

from database.connection import get_db
from database.models import Configuration, MCPServer, LLMProvider


class ConfigRepository:
    """Repository for managing application configuration and MCP servers."""

    # Configuration methods

    def get_config(self, key: str) -> Optional[Configuration]:
        """Get a configuration by key."""
        with get_db() as conn:
            row = conn.execute(
                "SELECT * FROM configurations WHERE key = ?",
                (key,),
            ).fetchone()

            if not row:
                return None

            return Configuration(
                key=row["key"],
                value=json.loads(row["value"]),
                category=row["category"],
            )

    def get_config_value(self, key: str, default: Any = None) -> Any:
        """Get a configuration value by key."""
        config = self.get_config(key)
        return config.value if config else default

    def set_config(self, key: str, value: dict[str, Any], category: str = "general") -> Configuration:
        """Set a configuration value."""
        config = Configuration(key=key, value=value, category=category)

        with get_db() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO configurations (key, value, category)
                VALUES (?, ?, ?)
                """,
                (key, json.dumps(value), category),
            )
            conn.commit()

        return config

    def delete_config(self, key: str) -> bool:
        """Delete a configuration."""
        with get_db() as conn:
            cursor = conn.execute(
                "DELETE FROM configurations WHERE key = ?",
                (key,),
            )
            conn.commit()
            return cursor.rowcount > 0

    def get_configs_by_category(self, category: str) -> list[Configuration]:
        """Get all configurations in a category."""
        with get_db() as conn:
            rows = conn.execute(
                "SELECT * FROM configurations WHERE category = ?",
                (category,),
            ).fetchall()

            return [
                Configuration(
                    key=row["key"],
                    value=json.loads(row["value"]),
                    category=row["category"],
                )
                for row in rows
            ]

    def get_all_configs(self) -> list[Configuration]:
        """Get all configurations."""
        with get_db() as conn:
            rows = conn.execute("SELECT * FROM configurations").fetchall()

            return [
                Configuration(
                    key=row["key"],
                    value=json.loads(row["value"]),
                    category=row["category"],
                )
                for row in rows
            ]

    # MCP Server methods

    def create_mcp_server(self, server: MCPServer) -> MCPServer:
        """Create a new MCP server."""
        with get_db() as conn:
            conn.execute(
                """
                INSERT INTO mcp_servers (id, name, transport_type, command, args, url, env, enabled, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    server.id,
                    server.name,
                    server.transport_type,
                    server.command,
                    json.dumps(server.args) if server.args else None,
                    server.url,
                    json.dumps(server.env) if server.env else None,
                    int(server.enabled),
                    server.created_at.isoformat(),
                    server.updated_at.isoformat(),
                ),
            )
            conn.commit()
        return server

    def get_mcp_server(self, server_id: str) -> Optional[MCPServer]:
        """Get an MCP server by ID."""
        with get_db() as conn:
            row = conn.execute(
                "SELECT * FROM mcp_servers WHERE id = ?",
                (server_id,),
            ).fetchone()

            if not row:
                return None

            return self._row_to_mcp_server(row)

    def get_mcp_server_by_name(self, name: str) -> Optional[MCPServer]:
        """Get an MCP server by name."""
        with get_db() as conn:
            row = conn.execute(
                "SELECT * FROM mcp_servers WHERE name = ?",
                (name,),
            ).fetchone()

            if not row:
                return None

            return self._row_to_mcp_server(row)

    def get_all_mcp_servers(self) -> list[MCPServer]:
        """Get all MCP servers."""
        with get_db() as conn:
            rows = conn.execute(
                "SELECT * FROM mcp_servers ORDER BY name"
            ).fetchall()
            return [self._row_to_mcp_server(row) for row in rows]

    def get_enabled_mcp_servers(self) -> list[MCPServer]:
        """Get all enabled MCP servers."""
        with get_db() as conn:
            rows = conn.execute(
                "SELECT * FROM mcp_servers WHERE enabled = 1 ORDER BY name"
            ).fetchall()
            return [self._row_to_mcp_server(row) for row in rows]

    def update_mcp_server(self, server: MCPServer) -> MCPServer:
        """Update an MCP server."""
        server.updated_at = datetime.utcnow()

        with get_db() as conn:
            conn.execute(
                """
                UPDATE mcp_servers
                SET name = ?, transport_type = ?, command = ?, args = ?, url = ?, env = ?, enabled = ?, updated_at = ?
                WHERE id = ?
                """,
                (
                    server.name,
                    server.transport_type,
                    server.command,
                    json.dumps(server.args) if server.args else None,
                    server.url,
                    json.dumps(server.env) if server.env else None,
                    int(server.enabled),
                    server.updated_at.isoformat(),
                    server.id,
                ),
            )
            conn.commit()
        return server

    def delete_mcp_server(self, server_id: str) -> bool:
        """Delete an MCP server."""
        with get_db() as conn:
            cursor = conn.execute(
                "DELETE FROM mcp_servers WHERE id = ?",
                (server_id,),
            )
            conn.commit()
            return cursor.rowcount > 0

    def enable_mcp_server(self, server_id: str) -> bool:
        """Enable an MCP server."""
        with get_db() as conn:
            cursor = conn.execute(
                """
                UPDATE mcp_servers
                SET enabled = 1, updated_at = ?
                WHERE id = ?
                """,
                (datetime.utcnow().isoformat(), server_id),
            )
            conn.commit()
            return cursor.rowcount > 0

    def disable_mcp_server(self, server_id: str) -> bool:
        """Disable an MCP server."""
        with get_db() as conn:
            cursor = conn.execute(
                """
                UPDATE mcp_servers
                SET enabled = 0, updated_at = ?
                WHERE id = ?
                """,
                (datetime.utcnow().isoformat(), server_id),
            )
            conn.commit()
            return cursor.rowcount > 0

    def _row_to_mcp_server(self, row) -> MCPServer:
        """Convert a database row to an MCPServer model."""
        return MCPServer(
            id=row["id"],
            name=row["name"],
            transport_type=row["transport_type"],
            command=row["command"],
            args=json.loads(row["args"]) if row["args"] else None,
            url=row["url"],
            env=json.loads(row["env"]) if row["env"] else None,
            enabled=bool(row["enabled"]),
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
        )

    # LLM Provider methods

    def create_llm_provider(self, provider: LLMProvider) -> LLMProvider:
        """Create a new LLM provider.

        Args:
            provider: The LLMProvider to create

        Returns:
            The created LLMProvider
        """
        with get_db() as conn:
            conn.execute(
                """
                INSERT INTO llm_providers (id, name, base_url, api_key, model, is_default, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    provider.id,
                    provider.name,
                    provider.base_url,
                    provider.api_key or "",
                    provider.model,
                    int(provider.is_default),
                    provider.created_at.isoformat(),
                    provider.updated_at.isoformat(),
                ),
            )
            conn.commit()
        return provider

    def get_llm_provider(self, name: str) -> Optional[LLMProvider]:
        """Get an LLM provider by name.

        Args:
            name: The provider name

        Returns:
            The LLMProvider or None if not found
        """
        with get_db() as conn:
            row = conn.execute(
                "SELECT * FROM llm_providers WHERE name = ?",
                (name,),
            ).fetchone()

            if not row:
                return None

            return self._row_to_llm_provider(row)

    def get_llm_provider_for_use(self, name: str) -> Optional[LLMProvider]:
        """Get an LLM provider for actual LLM calls.

        Args:
            name: The provider name

        Returns:
            The LLMProvider or None if not found
        """
        return self.get_llm_provider(name)

    def get_all_llm_providers(self) -> list[LLMProvider]:
        """Get all LLM providers.

        Returns:
            List of all LLMProviders
        """
        with get_db() as conn:
            rows = conn.execute(
                "SELECT * FROM llm_providers ORDER BY name"
            ).fetchall()
            return [self._row_to_llm_provider(row) for row in rows]

    def get_default_llm_provider(self) -> Optional[LLMProvider]:
        """Get the default LLM provider.

        Returns:
            The default LLMProvider or None if not found
        """
        with get_db() as conn:
            row = conn.execute(
                "SELECT * FROM llm_providers WHERE is_default = 1"
            ).fetchone()

            if not row:
                return None

            return self._row_to_llm_provider(row)

    def get_default_llm_provider_for_use(self) -> Optional[LLMProvider]:
        """Get the default LLM provider for actual LLM calls.

        Returns:
            The default LLMProvider or None if not found
        """
        return self.get_default_llm_provider()

    def update_llm_provider(
        self,
        provider: LLMProvider,
        new_api_key: Optional[str] = None,
    ) -> LLMProvider:
        """Update an LLM provider.

        Args:
            provider: The LLMProvider with updated fields
            new_api_key: New API key to set (None = keep existing key)

        Returns:
            The updated LLMProvider
        """
        provider.updated_at = datetime.utcnow()

        with get_db() as conn:
            if new_api_key is not None:
                # New API key provided - update it
                conn.execute(
                    """
                    UPDATE llm_providers
                    SET base_url = ?, api_key = ?, model = ?, is_default = ?, updated_at = ?
                    WHERE name = ?
                    """,
                    (
                        provider.base_url,
                        new_api_key,
                        provider.model,
                        int(provider.is_default),
                        provider.updated_at.isoformat(),
                        provider.name,
                    ),
                )
            else:
                # No new API key - preserve existing key
                conn.execute(
                    """
                    UPDATE llm_providers
                    SET base_url = ?, model = ?, is_default = ?, updated_at = ?
                    WHERE name = ?
                    """,
                    (
                        provider.base_url,
                        provider.model,
                        int(provider.is_default),
                        provider.updated_at.isoformat(),
                        provider.name,
                    ),
                )
            conn.commit()
        return provider

    def upsert_llm_provider(
        self,
        provider: LLMProvider,
        new_api_key: Optional[str] = None
    ) -> LLMProvider:
        """Create or update an LLM provider.

        Args:
            provider: The LLMProvider to create or update
            new_api_key: New API key to set (None = keep existing for update, use provider.api_key for create)

        Returns:
            The created or updated LLMProvider
        """
        existing = self.get_llm_provider(provider.name)
        if existing:
            # Preserve id from existing record
            provider.id = existing.id
            provider.created_at = existing.created_at
            return self.update_llm_provider(provider, new_api_key=new_api_key)
        # For new providers, use the api_key from provider if no new_api_key specified
        if new_api_key:
            provider.api_key = new_api_key
        return self.create_llm_provider(provider)

    def set_default_llm_provider(self, name: str) -> bool:
        """Set a provider as the default (unsets others)."""
        with get_db() as conn:
            # First, unset all defaults
            conn.execute("UPDATE llm_providers SET is_default = 0")

            # Set the new default
            cursor = conn.execute(
                """
                UPDATE llm_providers
                SET is_default = 1, updated_at = ?
                WHERE name = ?
                """,
                (datetime.utcnow().isoformat(), name),
            )
            conn.commit()
            return cursor.rowcount > 0

    def delete_llm_provider(self, name: str) -> bool:
        """Delete an LLM provider."""
        with get_db() as conn:
            cursor = conn.execute(
                "DELETE FROM llm_providers WHERE name = ?",
                (name,),
            )
            conn.commit()
            return cursor.rowcount > 0

    def _row_to_llm_provider(self, row) -> LLMProvider:
        """Convert a database row to an LLMProvider model.

        Args:
            row: The database row

        Returns:
            The LLMProvider model
        """
        return LLMProvider(
            id=row["id"],
            name=row["name"],
            base_url=row["base_url"],
            api_key=row["api_key"],
            model=row["model"],
            is_default=bool(row["is_default"]),
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
        )
