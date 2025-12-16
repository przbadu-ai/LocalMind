"""Repository for configuration and MCP server operations."""

import json
from datetime import datetime
from typing import Any, Optional

from backend.database.connection import get_db
from backend.database.models import Configuration, MCPServer


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
