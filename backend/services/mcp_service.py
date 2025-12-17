"""MCP (Model Context Protocol) server management service."""

import asyncio
import json
import logging
import subprocess
from typing import Any, Optional

from database.models import MCPServer
from database.repositories.config_repository import ConfigRepository

logger = logging.getLogger(__name__)


class MCPService:
    """Service for managing MCP servers."""

    def __init__(self):
        self.config_repo = ConfigRepository()
        self._running_processes: dict[str, subprocess.Popen] = {}
        self._server_status: dict[str, str] = {}  # server_id -> status

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
        if server_id in self._running_processes:
            self.stop_server(server_id)
        return self.config_repo.delete_mcp_server(server_id)

    def is_server_running(self, server_id: str) -> bool:
        """Check if a server is running."""
        if server_id not in self._running_processes:
            return False

        process = self._running_processes[server_id]
        return process.poll() is None

    def get_server_status(self, server_id: str) -> str:
        """Get the status of a server."""
        if self.is_server_running(server_id):
            return "running"
        return self._server_status.get(server_id, "stopped")

    async def start_server(self, server_id: str) -> bool:
        """Start an MCP server."""
        server = self.get_server(server_id)
        if not server:
            logger.error(f"Server {server_id} not found")
            return False

        if self.is_server_running(server_id):
            logger.info(f"Server {server_id} is already running")
            return True

        try:
            if server.transport_type == "stdio":
                return await self._start_stdio_server(server)
            elif server.transport_type == "sse":
                return await self._validate_sse_server(server)
            else:
                logger.error(f"Unknown transport type: {server.transport_type}")
                return False
        except Exception as e:
            logger.error(f"Failed to start server {server_id}: {e}")
            self._server_status[server_id] = f"error: {str(e)}"
            return False

    async def _start_stdio_server(self, server: MCPServer) -> bool:
        """Start a stdio-based MCP server."""
        if not server.command:
            logger.error(f"No command specified for stdio server {server.id}")
            return False

        # Build command
        cmd = [server.command]
        if server.args:
            cmd.extend(server.args)

        # Build environment
        env = dict(subprocess.os.environ)
        if server.env:
            env.update(server.env)

        try:
            process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=env,
            )
            self._running_processes[server.id] = process
            self._server_status[server.id] = "running"
            logger.info(f"Started stdio server {server.id}: {' '.join(cmd)}")
            return True
        except Exception as e:
            logger.error(f"Failed to start stdio server {server.id}: {e}")
            self._server_status[server.id] = f"error: {str(e)}"
            return False

    async def _validate_sse_server(self, server: MCPServer) -> bool:
        """Validate an SSE-based MCP server is reachable."""
        if not server.url:
            logger.error(f"No URL specified for SSE server {server.id}")
            return False

        try:
            import httpx

            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(server.url)
                if response.status_code == 200:
                    self._server_status[server.id] = "running"
                    logger.info(f"SSE server {server.id} is reachable at {server.url}")
                    return True
                else:
                    self._server_status[server.id] = f"error: HTTP {response.status_code}"
                    return False
        except Exception as e:
            logger.error(f"Failed to validate SSE server {server.id}: {e}")
            self._server_status[server.id] = f"error: {str(e)}"
            return False

    def stop_server(self, server_id: str) -> bool:
        """Stop a running MCP server."""
        if server_id not in self._running_processes:
            logger.info(f"Server {server_id} is not running")
            return True

        try:
            process = self._running_processes[server_id]
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()

            del self._running_processes[server_id]
            self._server_status[server_id] = "stopped"
            logger.info(f"Stopped server {server_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to stop server {server_id}: {e}")
            return False

    async def list_tools(self, server_id: str) -> list[dict[str, Any]]:
        """List available tools from an MCP server."""
        server = self.get_server(server_id)
        if not server:
            return []

        if not self.is_server_running(server_id) and server.transport_type == "stdio":
            return []

        try:
            # Send tools/list request via JSON-RPC
            request = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/list",
            }

            if server.transport_type == "stdio":
                return await self._send_stdio_request(server_id, request)
            else:
                return await self._send_sse_request(server, request)
        except Exception as e:
            logger.error(f"Failed to list tools for server {server_id}: {e}")
            return []

    async def call_tool(
        self,
        server_id: str,
        tool_name: str,
        arguments: dict[str, Any],
    ) -> dict[str, Any]:
        """Call a tool on an MCP server."""
        server = self.get_server(server_id)
        if not server:
            return {"error": "Server not found"}

        if not self.is_server_running(server_id) and server.transport_type == "stdio":
            return {"error": "Server not running"}

        try:
            request = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {
                    "name": tool_name,
                    "arguments": arguments,
                },
            }

            if server.transport_type == "stdio":
                return await self._send_stdio_request(server_id, request)
            else:
                return await self._send_sse_request(server, request)
        except Exception as e:
            logger.error(f"Failed to call tool {tool_name} on server {server_id}: {e}")
            return {"error": str(e)}

    async def _send_stdio_request(
        self,
        server_id: str,
        request: dict[str, Any],
    ) -> Any:
        """Send a JSON-RPC request to a stdio server."""
        if server_id not in self._running_processes:
            return {"error": "Server not running"}

        process = self._running_processes[server_id]
        if process.stdin is None or process.stdout is None:
            return {"error": "Server IO not available"}

        try:
            # Write request
            request_str = json.dumps(request) + "\n"
            process.stdin.write(request_str.encode())
            process.stdin.flush()

            # Read response (with timeout)
            loop = asyncio.get_event_loop()
            response_str = await asyncio.wait_for(
                loop.run_in_executor(None, process.stdout.readline),
                timeout=30.0,
            )

            if response_str:
                response = json.loads(response_str.decode())
                return response.get("result", response)
            return {"error": "No response"}
        except asyncio.TimeoutError:
            return {"error": "Request timed out"}
        except Exception as e:
            return {"error": str(e)}

    async def _send_sse_request(
        self,
        server: MCPServer,
        request: dict[str, Any],
    ) -> Any:
        """Send a JSON-RPC request to an SSE server."""
        if not server.url:
            return {"error": "No URL configured"}

        try:
            import httpx

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    server.url,
                    json=request,
                    headers={"Content-Type": "application/json"},
                )

                if response.status_code == 200:
                    data = response.json()
                    return data.get("result", data)
                else:
                    return {"error": f"HTTP {response.status_code}"}
        except Exception as e:
            return {"error": str(e)}

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
