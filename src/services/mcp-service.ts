/**
 * MCP (Model Context Protocol) service for managing MCP servers.
 *
 * This service provides methods for:
 * - Managing MCP server configurations
 * - Starting and stopping servers
 * - Listing and calling tools
 */

import { API_BASE_URL } from "@/config/app-config";

export interface MCPServer {
  id: string;
  name: string;
  description?: string;
  server_type: "stdio" | "sse";
  command?: string;
  args?: string[];
  url?: string;
  env?: Record<string, string>;
  is_enabled: boolean;
  created_at: string;
  updated_at?: string;
}

export interface MCPServerStatus {
  server_id: string;
  is_running: boolean;
  tools_count?: number;
  error?: string;
}

export interface MCPTool {
  name: string;
  description?: string;
  input_schema?: Record<string, unknown>;
}

export interface MCPToolCallResult {
  success: boolean;
  result?: unknown;
  error?: string;
}

export interface CreateMCPServerRequest {
  name: string;
  description?: string;
  server_type: "stdio" | "sse";
  command?: string;
  args?: string[];
  url?: string;
  env?: Record<string, string>;
  is_enabled?: boolean;
}

export interface UpdateMCPServerRequest {
  name?: string;
  description?: string;
  server_type?: "stdio" | "sse";
  command?: string;
  args?: string[];
  url?: string;
  env?: Record<string, string>;
  is_enabled?: boolean;
}

class MCPService {
  private baseUrl: string;

  constructor() {
    this.baseUrl = `${API_BASE_URL}/api/v1/mcp`;
  }

  /**
   * Get all configured MCP servers.
   */
  async getServers(): Promise<MCPServer[]> {
    const response = await fetch(`${this.baseUrl}/servers`, {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
      },
    });

    if (!response.ok) {
      throw new Error(`Failed to get servers: ${response.statusText}`);
    }

    return response.json();
  }

  /**
   * Get a specific MCP server by ID.
   */
  async getServer(serverId: string): Promise<MCPServer> {
    const response = await fetch(`${this.baseUrl}/servers/${serverId}`, {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
      },
    });

    if (!response.ok) {
      if (response.status === 404) {
        throw new Error("Server not found");
      }
      throw new Error(`Failed to get server: ${response.statusText}`);
    }

    return response.json();
  }

  /**
   * Create a new MCP server configuration.
   */
  async createServer(data: CreateMCPServerRequest): Promise<MCPServer> {
    const response = await fetch(`${this.baseUrl}/servers`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(data),
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(error.detail || `Failed to create server: ${response.statusText}`);
    }

    return response.json();
  }

  /**
   * Update an MCP server configuration.
   */
  async updateServer(
    serverId: string,
    data: UpdateMCPServerRequest
  ): Promise<MCPServer> {
    const response = await fetch(`${this.baseUrl}/servers/${serverId}`, {
      method: "PUT",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(data),
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(error.detail || `Failed to update server: ${response.statusText}`);
    }

    return response.json();
  }

  /**
   * Delete an MCP server configuration.
   */
  async deleteServer(serverId: string): Promise<void> {
    const response = await fetch(`${this.baseUrl}/servers/${serverId}`, {
      method: "DELETE",
      headers: {
        "Content-Type": "application/json",
      },
    });

    if (!response.ok) {
      throw new Error(`Failed to delete server: ${response.statusText}`);
    }
  }

  /**
   * Start an MCP server.
   */
  async startServer(serverId: string): Promise<MCPServerStatus> {
    const response = await fetch(`${this.baseUrl}/servers/${serverId}/start`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(error.detail || `Failed to start server: ${response.statusText}`);
    }

    return response.json();
  }

  /**
   * Stop an MCP server.
   */
  async stopServer(serverId: string): Promise<MCPServerStatus> {
    const response = await fetch(`${this.baseUrl}/servers/${serverId}/stop`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(error.detail || `Failed to stop server: ${response.statusText}`);
    }

    return response.json();
  }

  /**
   * Get the status of an MCP server.
   */
  async getServerStatus(serverId: string): Promise<MCPServerStatus> {
    const response = await fetch(`${this.baseUrl}/servers/${serverId}/status`, {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
      },
    });

    if (!response.ok) {
      return {
        server_id: serverId,
        is_running: false,
        error: response.statusText,
      };
    }

    return response.json();
  }

  /**
   * Get available tools from an MCP server.
   */
  async getTools(serverId: string): Promise<MCPTool[]> {
    const response = await fetch(`${this.baseUrl}/servers/${serverId}/tools`, {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
      },
    });

    if (!response.ok) {
      throw new Error(`Failed to get tools: ${response.statusText}`);
    }

    const data = await response.json();
    return data.tools || [];
  }

  /**
   * Call a tool on an MCP server.
   */
  async callTool(
    serverId: string,
    toolName: string,
    args?: Record<string, unknown>
  ): Promise<MCPToolCallResult> {
    const response = await fetch(
      `${this.baseUrl}/servers/${serverId}/tools/${toolName}`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ arguments: args || {} }),
      }
    );

    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      return {
        success: false,
        error: error.detail || response.statusText,
      };
    }

    const result = await response.json();
    return {
      success: true,
      result: result.result,
    };
  }
}

// Export singleton instance
export const mcpService = new MCPService();
export default mcpService;
