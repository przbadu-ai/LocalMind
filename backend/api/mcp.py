"""MCP server management API endpoints."""

from typing import Any, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from database.models import MCPServer
from services.mcp_service import mcp_service

router = APIRouter()


class CreateMCPServerRequest(BaseModel):
    """Request body for creating an MCP server."""

    name: str
    transport_type: str  # "stdio" or "sse"
    command: Optional[str] = None
    args: Optional[list[str]] = None
    url: Optional[str] = None
    env: Optional[dict[str, str]] = None
    enabled: bool = True


class UpdateMCPServerRequest(BaseModel):
    """Request body for updating an MCP server."""

    name: Optional[str] = None
    transport_type: Optional[str] = None
    command: Optional[str] = None
    args: Optional[list[str]] = None
    url: Optional[str] = None
    env: Optional[dict[str, str]] = None
    enabled: Optional[bool] = None


class MCPServerResponse(BaseModel):
    """Response model for an MCP server."""

    id: str
    name: str
    transport_type: str
    command: Optional[str] = None
    args: Optional[list[str]] = None
    url: Optional[str] = None
    env: Optional[dict[str, str]] = None
    enabled: bool
    status: str
    created_at: str
    updated_at: str


class CallToolRequest(BaseModel):
    """Request body for calling an MCP tool."""

    arguments: dict[str, Any] = {}


def _server_to_response(server: MCPServer) -> MCPServerResponse:
    """Convert MCPServer to response model."""
    return MCPServerResponse(
        id=server.id,
        name=server.name,
        transport_type=server.transport_type,
        command=server.command,
        args=server.args,
        url=server.url,
        env=server.env,
        enabled=server.enabled,
        status=mcp_service.get_server_status(server.id),
        created_at=server.created_at.isoformat(),
        updated_at=server.updated_at.isoformat(),
    )


@router.get("/mcp/servers")
async def list_mcp_servers() -> list[MCPServerResponse]:
    """List all configured MCP servers."""
    servers = mcp_service.get_all_servers()
    return [_server_to_response(s) for s in servers]


@router.post("/mcp/servers")
async def create_mcp_server(request: CreateMCPServerRequest) -> MCPServerResponse:
    """Create a new MCP server configuration."""
    # Validate transport type
    if request.transport_type not in ("stdio", "sse"):
        raise HTTPException(
            status_code=400,
            detail="transport_type must be 'stdio' or 'sse'",
        )

    # Validate required fields based on transport type
    if request.transport_type == "stdio" and not request.command:
        raise HTTPException(
            status_code=400,
            detail="command is required for stdio transport",
        )

    if request.transport_type == "sse" and not request.url:
        raise HTTPException(
            status_code=400,
            detail="url is required for sse transport",
        )

    server = MCPServer(
        name=request.name,
        transport_type=request.transport_type,
        command=request.command,
        args=request.args,
        url=request.url,
        env=request.env,
        enabled=request.enabled,
    )

    try:
        server = mcp_service.create_server(server)
        return _server_to_response(server)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/mcp/servers/{server_id}")
async def get_mcp_server(server_id: str) -> MCPServerResponse:
    """Get an MCP server by ID."""
    server = mcp_service.get_server(server_id)
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")

    return _server_to_response(server)


@router.put("/mcp/servers/{server_id}")
async def update_mcp_server(
    server_id: str,
    request: UpdateMCPServerRequest,
) -> MCPServerResponse:
    """Update an MCP server configuration."""
    server = mcp_service.get_server(server_id)
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")

    # Update fields
    if request.name is not None:
        server.name = request.name
    if request.transport_type is not None:
        if request.transport_type not in ("stdio", "sse"):
            raise HTTPException(
                status_code=400,
                detail="transport_type must be 'stdio' or 'sse'",
            )
        server.transport_type = request.transport_type
    if request.command is not None:
        server.command = request.command
    if request.args is not None:
        server.args = request.args
    if request.url is not None:
        server.url = request.url
    if request.env is not None:
        server.env = request.env
    if request.enabled is not None:
        server.enabled = request.enabled

    server = mcp_service.update_server(server)
    return _server_to_response(server)


@router.delete("/mcp/servers/{server_id}")
async def delete_mcp_server(server_id: str) -> dict:
    """Delete an MCP server configuration."""
    if not mcp_service.delete_server(server_id):
        raise HTTPException(status_code=404, detail="Server not found")

    return {"success": True, "message": "Server deleted"}


@router.post("/mcp/servers/{server_id}/start")
async def start_mcp_server(server_id: str) -> dict:
    """Start an MCP server."""
    server = mcp_service.get_server(server_id)
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")

    success = await mcp_service.start_server(server_id)

    return {
        "success": success,
        "status": mcp_service.get_server_status(server_id),
    }


@router.post("/mcp/servers/{server_id}/stop")
async def stop_mcp_server(server_id: str) -> dict:
    """Stop a running MCP server."""
    server = mcp_service.get_server(server_id)
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")

    success = await mcp_service.stop_server(server_id)

    return {
        "success": success,
        "status": mcp_service.get_server_status(server_id),
    }


@router.get("/mcp/servers/{server_id}/tools")
async def list_mcp_tools(server_id: str) -> list[dict]:
    """List available tools from an MCP server."""
    server = mcp_service.get_server(server_id)
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")

    tools = await mcp_service.list_tools(server_id)
    return tools


@router.post("/mcp/servers/{server_id}/tools/{tool_name}")
async def call_mcp_tool(
    server_id: str,
    tool_name: str,
    request: CallToolRequest,
) -> dict:
    """Call a tool on an MCP server."""
    server = mcp_service.get_server(server_id)
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")

    result = await mcp_service.call_tool(server_id, tool_name, request.arguments)
    return result


@router.get("/mcp/config")
async def get_mcp_config() -> dict:
    """Get MCP configuration JSON for external tools."""
    config_json = mcp_service.create_mcp_config_json()
    return {"config": config_json}


class BulkImportRequest(BaseModel):
    """Request body for bulk importing MCP servers from JSON."""

    mcpServers: dict[str, dict]  # Standard MCP config format


@router.post("/mcp/import")
async def import_mcp_servers(request: BulkImportRequest) -> dict:
    """Import MCP servers from standard MCP JSON configuration format.

    Accepts the standard mcpServers format:
    {
        "mcpServers": {
            "server-name": {
                "command": "npx",
                "args": ["-y", "@modelcontextprotocol/server-filesystem"],
                "env": {"KEY": "value"}
            }
        }
    }
    """
    imported = []
    errors = []

    for name, config in request.mcpServers.items():
        try:
            # Determine transport type
            if "command" in config:
                transport_type = "stdio"
            elif "url" in config:
                transport_type = "sse"
            else:
                errors.append({"name": name, "error": "Missing 'command' or 'url'"})
                continue

            # Check if server with same name exists
            existing = None
            for s in mcp_service.get_all_servers():
                if s.name == name:
                    existing = s
                    break

            if existing:
                # Update existing server
                existing.transport_type = transport_type
                existing.command = config.get("command")
                existing.args = config.get("args", [])
                existing.url = config.get("url")
                existing.env = config.get("env", {})
                mcp_service.update_server(existing)
                imported.append({"name": name, "action": "updated"})
            else:
                # Create new server
                server = MCPServer(
                    name=name,
                    transport_type=transport_type,
                    command=config.get("command"),
                    args=config.get("args", []),
                    url=config.get("url"),
                    env=config.get("env", {}),
                    enabled=True,
                )
                mcp_service.create_server(server)
                imported.append({"name": name, "action": "created"})

        except Exception as e:
            errors.append({"name": name, "error": str(e)})

    return {
        "success": len(errors) == 0,
        "imported": imported,
        "errors": errors,
        "message": f"Imported {len(imported)} server(s)" + (f", {len(errors)} error(s)" if errors else "")
    }


@router.get("/mcp/export")
async def export_mcp_servers() -> dict:
    """Export all MCP servers in standard MCP JSON configuration format."""
    servers = mcp_service.get_all_servers()

    mcp_servers = {}
    for server in servers:
        config = {}
        if server.transport_type == "stdio":
            config["command"] = server.command
            if server.args:
                config["args"] = server.args
        else:
            config["url"] = server.url

        if server.env:
            config["env"] = server.env

        mcp_servers[server.name] = config

    return {"mcpServers": mcp_servers}
