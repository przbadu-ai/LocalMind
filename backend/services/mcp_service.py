"""MCP (Model Context Protocol) server management service using official SDK."""

import asyncio
import json
import logging
from contextlib import AsyncExitStack
from typing import Any, Optional

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from database.models import MCPServer
from database.repositories.config_repository import ConfigRepository

logger = logging.getLogger(__name__)


class MCPServerConnection:
    """Manages a single MCP server connection using the official SDK."""

    def __init__(self, server: MCPServer):
        self.server = server
        self.session: Optional[ClientSession] = None
        self.exit_stack: Optional[AsyncExitStack] = None
        self._tools_cache: Optional[list[dict[str, Any]]] = None

    async def connect(self) -> bool:
        """Connect to the MCP server."""
        if self.session is not None:
            return True

        try:
            self.exit_stack = AsyncExitStack()

            if self.server.transport_type == "stdio":
                return await self._connect_stdio()
            else:
                logger.error(f"Unsupported transport type: {self.server.transport_type}")
                return False

        except Exception as e:
            logger.error(f"Failed to connect to MCP server {self.server.name}: {e}")
            await self.disconnect()
            return False

    async def _connect_stdio(self) -> bool:
        """Connect to a stdio-based MCP server."""
        if not self.server.command:
            logger.error(f"No command specified for stdio server {self.server.name}")
            return False

        # Build args list
        args = self.server.args or []

        # Build environment
        env = dict(self.server.env) if self.server.env else None

        server_params = StdioServerParameters(
            command=self.server.command,
            args=args,
            env=env,
        )

        try:
            # Use the official MCP SDK's stdio_client with timeout
            # This prevents hanging if the server process crashes or hangs during startup
            stdio_transport = await asyncio.wait_for(
                self.exit_stack.enter_async_context(stdio_client(server_params)),
                timeout=30.0
            )
            read_stream, write_stream = stdio_transport

            # Create and initialize session with timeout
            self.session = await asyncio.wait_for(
                self.exit_stack.enter_async_context(ClientSession(read_stream, write_stream)),
                timeout=10.0
            )

            # Initialize the MCP session (required handshake) with timeout
            await asyncio.wait_for(self.session.initialize(), timeout=30.0)

            logger.info(f"Connected to MCP server: {self.server.name}")
            return True

        except asyncio.TimeoutError:
            logger.error(f"Timeout connecting to MCP server {self.server.name}")
            return False
        except Exception as e:
            logger.error(f"Failed to start stdio server {self.server.name}: {e}")
            return False

    async def disconnect(self) -> None:
        """Disconnect from the MCP server."""
        if self.exit_stack:
            try:
                await self.exit_stack.aclose()
            except Exception as e:
                logger.warning(f"Error closing MCP server {self.server.name}: {e}")
            finally:
                self.exit_stack = None
                self.session = None
                self._tools_cache = None

    async def list_tools(self) -> list[dict[str, Any]]:
        """List available tools from the MCP server."""
        if not self.session:
            return []

        try:
            # Add timeout to prevent hanging
            response = await asyncio.wait_for(
                self.session.list_tools(),
                timeout=30.0
            )
            tools = []
            for tool in response.tools:
                tools.append({
                    "name": tool.name,
                    "description": tool.description or "",
                    "inputSchema": tool.inputSchema if hasattr(tool, 'inputSchema') else {},
                })
            self._tools_cache = tools
            logger.info(f"Listed {len(tools)} tools from {self.server.name}")
            return tools
        except asyncio.TimeoutError:
            logger.error(f"Timeout listing tools from {self.server.name}")
            return []
        except Exception as e:
            logger.error(f"Failed to list tools from {self.server.name}: {e}")
            return []

    async def call_tool(self, tool_name: str, arguments: dict[str, Any]) -> Any:
        """Call a tool on the MCP server."""
        if not self.session:
            return {"error": "Server not connected"}

        logger.info(f"Calling tool {tool_name} on {self.server.name} with args: {arguments}")

        try:
            # Add timeout to prevent hanging (60s for tool execution)
            result = await asyncio.wait_for(
                self.session.call_tool(tool_name, arguments),
                timeout=60.0
            )

            # Extract content from the result
            if hasattr(result, 'content') and result.content:
                # MCP returns content as a list of content blocks
                contents = []
                for content in result.content:
                    if hasattr(content, 'text'):
                        contents.append(content.text)
                    elif hasattr(content, 'data'):
                        contents.append(content.data)
                    else:
                        contents.append(str(content))

                if len(contents) == 1:
                    logger.info(f"Tool {tool_name} returned: {contents[0][:200]}...")
                    return contents[0]
                logger.info(f"Tool {tool_name} returned {len(contents)} content blocks")
                return contents

            return result

        except asyncio.TimeoutError:
            logger.error(f"Timeout calling tool {tool_name} on {self.server.name}")
            return {"error": f"Tool {tool_name} execution timed out after 60s"}
        except Exception as e:
            logger.error(f"Failed to call tool {tool_name} on {self.server.name}: {e}")
            return {"error": str(e)}

    @property
    def is_connected(self) -> bool:
        """Check if the server is connected."""
        return self.session is not None


class MCPService:
    """Service for managing MCP servers using the official SDK."""

    def __init__(self):
        self.config_repo = ConfigRepository()
        self._connections: dict[str, MCPServerConnection] = {}
        self._server_status: dict[str, str] = {}

    def get_all_servers(self) -> list[MCPServer]:
        """Get all configured MCP servers."""
        return self.config_repo.get_all_mcp_servers()

    def get_enabled_servers(self) -> list[MCPServer]:
        """Get all enabled MCP servers."""
        return self.config_repo.get_enabled_mcp_servers()

    def get_server(self, server_id: str) -> Optional[MCPServer]:
        """Get a server by ID."""
        return self.config_repo.get_mcp_server(server_id)

    def create_server(self, server: MCPServer) -> MCPServer:
        """Create a new MCP server configuration."""
        return self.config_repo.create_mcp_server(server)

    def update_server(self, server: MCPServer) -> MCPServer:
        """Update an MCP server configuration."""
        return self.config_repo.update_mcp_server(server)

    def delete_server(self, server_id: str) -> bool:
        """Delete an MCP server configuration."""
        # Stop the server if it's running
        if server_id in self._connections:
            asyncio.create_task(self.stop_server(server_id))
        return self.config_repo.delete_mcp_server(server_id)

    def is_server_running(self, server_id: str) -> bool:
        """Check if a server is running."""
        conn = self._connections.get(server_id)
        return conn is not None and conn.is_connected

    def get_server_status(self, server_id: str) -> str:
        """Get the status of a server."""
        if self.is_server_running(server_id):
            return "running"
        return self._server_status.get(server_id, "stopped")

    async def start_server(self, server_id: str) -> bool:
        """Start an MCP server.

        This method is designed to never crash - it returns False on failure
        and logs the error, allowing other servers to continue starting.
        """
        server = self.get_server(server_id)
        if not server:
            logger.error(f"Server {server_id} not found")
            return False

        if self.is_server_running(server_id):
            logger.info(f"Server {server_id} is already running")
            return True

        conn = None
        try:
            conn = MCPServerConnection(server)
            success = await conn.connect()

            if success:
                self._connections[server_id] = conn
                self._server_status[server_id] = "running"
                logger.info(f"Started MCP server: {server.name}")
                return True
            else:
                # Clean up failed connection
                if conn:
                    try:
                        await conn.disconnect()
                    except Exception:
                        pass
                self._server_status[server_id] = "error: failed to connect"
                logger.warning(f"MCP server {server.name} failed to start (check server logs above)")
                return False

        except Exception as e:
            # Clean up on exception
            if conn:
                try:
                    await conn.disconnect()
                except Exception:
                    pass
            error_msg = str(e)
            logger.error(f"Failed to start server {server.name}: {error_msg}")
            self._server_status[server_id] = f"error: {error_msg[:100]}"
            return False

    async def stop_server(self, server_id: str) -> bool:
        """Stop a running MCP server."""
        conn = self._connections.get(server_id)
        if not conn:
            logger.info(f"Server {server_id} is not running")
            return True

        try:
            await conn.disconnect()
            del self._connections[server_id]
            self._server_status[server_id] = "stopped"
            logger.info(f"Stopped server {server_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to stop server {server_id}: {e}")
            return False

    async def list_tools(self, server_id: str) -> list[dict[str, Any]]:
        """List available tools from an MCP server."""
        conn = self._connections.get(server_id)
        if not conn or not conn.is_connected:
            return []

        return await conn.list_tools()

    async def call_tool(
        self,
        server_id: str,
        tool_name: str,
        arguments: dict[str, Any],
    ) -> Any:
        """Call a tool on an MCP server."""
        conn = self._connections.get(server_id)
        if not conn or not conn.is_connected:
            return {"error": "Server not running"}

        return await conn.call_tool(tool_name, arguments)

    async def get_all_tools_as_openai_format(self) -> tuple[list[dict[str, Any]], dict[str, str]]:
        """Get all tools from enabled/running MCP servers in OpenAI function format.

        Returns:
            Tuple of (tools_list, tool_to_server_map) where:
            - tools_list: List of tools in OpenAI function format
            - tool_to_server_map: Dict mapping tool name to server_id
        """
        all_tools: list[dict[str, Any]] = []
        tool_to_server: dict[str, str] = {}

        for server_id, conn in self._connections.items():
            if not conn.is_connected:
                continue

            try:
                tools = await conn.list_tools()
                for tool in tools:
                    openai_tool = self._convert_mcp_tool_to_openai(tool, conn.server.name)
                    if openai_tool:
                        all_tools.append(openai_tool)
                        tool_name = openai_tool["function"]["name"]
                        tool_to_server[tool_name] = server_id
            except Exception as e:
                logger.warning(f"Failed to get tools from server {conn.server.name}: {e}")

        return all_tools, tool_to_server

    def _convert_mcp_tool_to_openai(
        self, mcp_tool: dict[str, Any], server_name: str
    ) -> Optional[dict[str, Any]]:
        """Convert an MCP tool definition to OpenAI function format."""
        try:
            tool_name = mcp_tool.get("name")
            if not tool_name:
                return None

            # Prefix tool name with server name to avoid collisions
            prefixed_name = f"{server_name}__{tool_name}"

            function_def: dict[str, Any] = {
                "name": prefixed_name,
                "description": mcp_tool.get("description", f"Tool from {server_name}"),
            }

            # Convert input schema
            input_schema = mcp_tool.get("inputSchema", mcp_tool.get("input_schema", {}))
            if input_schema:
                function_def["parameters"] = {
                    "type": input_schema.get("type", "object"),
                    "properties": input_schema.get("properties", {}),
                    "required": input_schema.get("required", []),
                }
            else:
                function_def["parameters"] = {
                    "type": "object",
                    "properties": {},
                }

            return {
                "type": "function",
                "function": function_def,
            }

        except Exception as e:
            logger.warning(f"Failed to convert MCP tool to OpenAI format: {e}")
            return None

    def parse_tool_name(self, prefixed_name: str) -> tuple[str, str]:
        """Parse a prefixed tool name back to server_name and tool_name."""
        if "__" in prefixed_name:
            parts = prefixed_name.split("__", 1)
            return parts[0], parts[1]
        return "", prefixed_name

    def create_mcp_config_json(self, servers: Optional[list[MCPServer]] = None) -> str:
        """Generate MCP configuration JSON for external tools."""
        if servers is None:
            servers = self.get_enabled_servers()

        config = {"mcpServers": {}}

        for server in servers:
            server_config: dict[str, Any] = {}

            if server.transport_type == "stdio":
                server_config["command"] = server.command
                if server.args:
                    server_config["args"] = server.args
                if server.env:
                    server_config["env"] = server.env
            else:
                server_config["url"] = server.url

            config["mcpServers"][server.name] = server_config

        return json.dumps(config, indent=2)


# Global MCP service instance
mcp_service = MCPService()
