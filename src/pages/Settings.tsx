import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Switch } from "@/components/ui/switch"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Badge } from "@/components/ui/badge"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Separator } from "@/components/ui/separator"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"
import {
  AlertCircle,
  CheckCircle2,
  Loader2,
  Plus,
  Trash2,
  Play,
  Square,
  RefreshCw,
  Server,
  Cpu,
  Eye,
  EyeOff,
} from "lucide-react"
import { API_BASE_URL } from "@/config/app-config"
import { useHeaderStore } from "@/stores/useHeaderStore"

interface LLMSettings {
  provider: string
  base_url: string
  api_key: string
  model: string
  available: boolean
}

// Provider configurations with default URLs
const PROVIDER_CONFIGS: Record<string, { url: string; requiresApiKey: boolean; placeholder: string }> = {
  ollama: {
    url: "http://localhost:11434/v1",
    requiresApiKey: false,
    placeholder: "llama3:instruct",
  },
  openai: {
    url: "https://api.openai.com/v1",
    requiresApiKey: true,
    placeholder: "gpt-4o",
  },
  openai_compatible: {
    url: "http://localhost:8080/v1",
    requiresApiKey: false,
    placeholder: "model-name",
  },
  gemini: {
    url: "https://generativelanguage.googleapis.com/v1beta/openai",
    requiresApiKey: true,
    placeholder: "gemini-2.0-flash",
  },
  cerebras: {
    url: "https://api.cerebras.ai/v1",
    requiresApiKey: true,
    placeholder: "llama-4-scout-17b-16e-instruct",
  },
  claude: {
    url: "https://api.anthropic.com/v1",
    requiresApiKey: true,
    placeholder: "claude-sonnet-4-20250514",
  },
  mistral: {
    url: "https://api.mistral.ai/v1",
    requiresApiKey: true,
    placeholder: "mistral-large-latest",
  },
}

interface MCPServer {
  id: string
  name: string
  transport_type: "stdio" | "sse"
  command?: string
  args?: string[]
  url?: string
  env?: Record<string, string>
  enabled: boolean
  status: string
  created_at: string
  updated_at: string
}

export default function Settings() {
  const { setTitle } = useHeaderStore()

  // LLM Settings state
  const [llmSettings, setLlmSettings] = useState<LLMSettings | null>(null)
  const [llmLoading, setLlmLoading] = useState(true)
  const [llmSaving, setLlmSaving] = useState(false)
  const [llmTesting, setLlmTesting] = useState(false)
  const [llmTestResult, setLlmTestResult] = useState<{ success: boolean; message: string } | null>(null)
  const [availableModels, setAvailableModels] = useState<string[]>([])
  const [showApiKey, setShowApiKey] = useState(false)

  // MCP Servers state
  const [mcpServers, setMcpServers] = useState<MCPServer[]>([])
  const [mcpLoading, setMcpLoading] = useState(true)
  const [showAddServer, setShowAddServer] = useState(false)
  const [newServer, setNewServer] = useState({
    name: "",
    transport_type: "stdio" as "stdio" | "sse",
    command: "",
    args: "",
    url: "",
    enabled: true,
  })

  // Form state for editing
  const [editedLlm, setEditedLlm] = useState({
    provider: "",
    base_url: "",
    api_key: "",
    model: "",
  })

  useEffect(() => {
    setTitle("Settings")
    loadLLMSettings()
    loadMCPServers()
  }, [setTitle])

  // Load LLM settings
  const loadLLMSettings = async () => {
    try {
      setLlmLoading(true)
      const response = await fetch(`${API_BASE_URL}/api/v1/settings/llm`)
      if (response.ok) {
        const data = await response.json()
        setLlmSettings(data)
        setEditedLlm({
          provider: data.provider,
          base_url: data.base_url,
          api_key: "",  // Don't show masked key
          model: data.model,
        })
      }
    } catch (error) {
      console.error("Failed to load LLM settings:", error)
    } finally {
      setLlmLoading(false)
    }
  }

  // Load available models
  const loadAvailableModels = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/settings/llm/models`)
      if (response.ok) {
        const data = await response.json()
        setAvailableModels(data.models || [])
      }
    } catch (error) {
      console.error("Failed to load models:", error)
    }
  }

  // Save LLM settings
  const saveLLMSettings = async () => {
    try {
      setLlmSaving(true)
      const payload: any = {}
      if (editedLlm.provider) payload.provider = editedLlm.provider
      if (editedLlm.base_url) payload.base_url = editedLlm.base_url
      if (editedLlm.api_key) payload.api_key = editedLlm.api_key
      if (editedLlm.model) payload.model = editedLlm.model

      const response = await fetch(`${API_BASE_URL}/api/v1/settings/llm`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      })

      if (response.ok) {
        await loadLLMSettings()
        setLlmTestResult({ success: true, message: "Settings saved successfully" })
      } else {
        setLlmTestResult({ success: false, message: "Failed to save settings" })
      }
    } catch (error) {
      setLlmTestResult({ success: false, message: `Error: ${error}` })
    } finally {
      setLlmSaving(false)
    }
  }

  // Test LLM connection
  const testLLMConnection = async () => {
    try {
      setLlmTesting(true)
      setLlmTestResult(null)

      const response = await fetch(`${API_BASE_URL}/api/v1/settings/llm/test`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          base_url: editedLlm.base_url || undefined,
          api_key: editedLlm.api_key || undefined,
          model: editedLlm.model || undefined,
        }),
      })

      const data = await response.json()
      setLlmTestResult({ success: data.success, message: data.message })

      if (data.models && data.models.length > 0) {
        setAvailableModels(data.models)
      }
    } catch (error) {
      setLlmTestResult({ success: false, message: `Connection failed: ${error}` })
    } finally {
      setLlmTesting(false)
    }
  }

  // Load MCP servers
  const loadMCPServers = async () => {
    try {
      setMcpLoading(true)
      const response = await fetch(`${API_BASE_URL}/api/v1/mcp/servers`)
      if (response.ok) {
        const data = await response.json()
        setMcpServers(data)
      }
    } catch (error) {
      console.error("Failed to load MCP servers:", error)
    } finally {
      setMcpLoading(false)
    }
  }

  // Add MCP server
  const addMCPServer = async () => {
    try {
      const payload: any = {
        name: newServer.name,
        transport_type: newServer.transport_type,
        enabled: newServer.enabled,
      }

      if (newServer.transport_type === "stdio") {
        payload.command = newServer.command
        payload.args = newServer.args ? newServer.args.split(" ").filter(Boolean) : []
      } else {
        payload.url = newServer.url
      }

      const response = await fetch(`${API_BASE_URL}/api/v1/mcp/servers`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      })

      if (response.ok) {
        setShowAddServer(false)
        setNewServer({
          name: "",
          transport_type: "stdio",
          command: "",
          args: "",
          url: "",
          enabled: true,
        })
        await loadMCPServers()
      }
    } catch (error) {
      console.error("Failed to add MCP server:", error)
    }
  }

  // Delete MCP server
  const deleteMCPServer = async (serverId: string) => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/mcp/servers/${serverId}`, {
        method: "DELETE",
      })

      if (response.ok) {
        await loadMCPServers()
      }
    } catch (error) {
      console.error("Failed to delete MCP server:", error)
    }
  }

  // Start/Stop MCP server
  const toggleMCPServer = async (serverId: string, action: "start" | "stop") => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/mcp/servers/${serverId}/${action}`, {
        method: "POST",
      })

      if (response.ok) {
        await loadMCPServers()
      }
    } catch (error) {
      console.error(`Failed to ${action} MCP server:`, error)
    }
  }

  return (
    <div className="h-full flex flex-col">
      <ScrollArea className="flex-1">
        <div className="p-6 max-w-4xl mx-auto space-y-6">
          <div>
            <h1 className="text-2xl font-semibold">Settings</h1>
            <p className="text-muted-foreground mt-1">
              Configure your LLM provider and MCP servers
            </p>
          </div>

          <Tabs defaultValue="llm" className="space-y-6">
            <TabsList>
              <TabsTrigger value="llm" className="flex items-center gap-2">
                <Cpu className="h-4 w-4" />
                LLM Configuration
              </TabsTrigger>
              <TabsTrigger value="mcp" className="flex items-center gap-2">
                <Server className="h-4 w-4" />
                MCP Servers
              </TabsTrigger>
            </TabsList>

            {/* LLM Configuration Tab */}
            <TabsContent value="llm" className="space-y-4">
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center justify-between">
                    <span>LLM Provider Settings</span>
                    {llmSettings && (
                      <Badge variant={llmSettings.available ? "default" : "destructive"}>
                        {llmSettings.available ? (
                          <><CheckCircle2 className="h-3 w-3 mr-1" /> Connected</>
                        ) : (
                          <><AlertCircle className="h-3 w-3 mr-1" /> Disconnected</>
                        )}
                      </Badge>
                    )}
                  </CardTitle>
                  <CardDescription>
                    Configure your OpenAI-compatible LLM endpoint (Ollama, LlamaCpp, vLLM, etc.)
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  {llmLoading ? (
                    <div className="flex items-center justify-center py-8">
                      <Loader2 className="h-6 w-6 animate-spin" />
                    </div>
                  ) : (
                    <>
                      <div className="grid gap-4">
                        <div className="grid gap-2">
                          <Label htmlFor="provider">Provider</Label>
                          <Select
                            value={editedLlm.provider}
                            onValueChange={(value) => {
                              const config = PROVIDER_CONFIGS[value]
                              setEditedLlm(prev => ({
                                ...prev,
                                provider: value,
                                base_url: config?.url || prev.base_url,
                                model: config?.placeholder || prev.model,
                              }))
                            }}
                          >
                            <SelectTrigger>
                              <SelectValue placeholder="Select provider" />
                            </SelectTrigger>
                            <SelectContent>
                              <SelectItem value="ollama">Ollama</SelectItem>
                              <SelectItem value="openai">OpenAI</SelectItem>
                              <SelectItem value="gemini">Google Gemini</SelectItem>
                              <SelectItem value="cerebras">Cerebras</SelectItem>
                              <SelectItem value="claude">Claude (Anthropic)</SelectItem>
                              <SelectItem value="mistral">Mistral AI</SelectItem>
                              <SelectItem value="openai_compatible">OpenAI Compatible</SelectItem>
                            </SelectContent>
                          </Select>
                        </div>

                        <div className="grid gap-2">
                          <Label htmlFor="base_url">Base URL</Label>
                          <Input
                            id="base_url"
                            value={editedLlm.base_url}
                            onChange={(e) => setEditedLlm(prev => ({ ...prev, base_url: e.target.value }))}
                            placeholder={PROVIDER_CONFIGS[editedLlm.provider]?.url || "http://localhost:11434/v1"}
                          />
                          <p className="text-xs text-muted-foreground">
                            OpenAI-compatible API endpoint
                          </p>
                        </div>

                        <div className="grid gap-2">
                          <Label htmlFor="api_key">
                            API Key
                            {PROVIDER_CONFIGS[editedLlm.provider]?.requiresApiKey && (
                              <span className="text-red-500 ml-1">*</span>
                            )}
                          </Label>
                          <div className="flex gap-2">
                            <Input
                              id="api_key"
                              type={showApiKey ? "text" : "password"}
                              value={editedLlm.api_key}
                              onChange={(e) => setEditedLlm(prev => ({ ...prev, api_key: e.target.value }))}
                              placeholder={
                                PROVIDER_CONFIGS[editedLlm.provider]?.requiresApiKey
                                  ? "Required - Enter your API key"
                                  : "Optional for local providers"
                              }
                            />
                            <Button
                              variant="outline"
                              size="icon"
                              onClick={() => setShowApiKey(!showApiKey)}
                            >
                              {showApiKey ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                            </Button>
                          </div>
                        </div>

                        <div className="grid gap-2">
                          <Label htmlFor="model">Model</Label>
                          <div className="flex gap-2">
                            <Input
                              id="model"
                              value={editedLlm.model}
                              onChange={(e) => setEditedLlm(prev => ({ ...prev, model: e.target.value }))}
                              placeholder={PROVIDER_CONFIGS[editedLlm.provider]?.placeholder || "Enter model name"}
                              list="available-models"
                            />
                            <datalist id="available-models">
                              {availableModels.map((model) => (
                                <option key={model} value={model} />
                              ))}
                            </datalist>
                            <Button
                              variant="outline"
                              size="icon"
                              onClick={loadAvailableModels}
                              title="Refresh models"
                            >
                              <RefreshCw className="h-4 w-4" />
                            </Button>
                          </div>
                          {availableModels.length > 0 && (
                            <p className="text-xs text-muted-foreground">
                              {availableModels.length} models available
                            </p>
                          )}
                        </div>
                      </div>

                      {llmTestResult && (
                        <div className={`flex items-center gap-2 p-3 rounded-lg ${
                          llmTestResult.success ? "bg-green-500/10 text-green-600" : "bg-red-500/10 text-red-600"
                        }`}>
                          {llmTestResult.success ? (
                            <CheckCircle2 className="h-4 w-4" />
                          ) : (
                            <AlertCircle className="h-4 w-4" />
                          )}
                          <span className="text-sm">{llmTestResult.message}</span>
                        </div>
                      )}

                      <Separator />

                      <div className="flex justify-end gap-2">
                        <Button
                          variant="outline"
                          onClick={testLLMConnection}
                          disabled={llmTesting}
                        >
                          {llmTesting ? (
                            <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                          ) : (
                            <RefreshCw className="h-4 w-4 mr-2" />
                          )}
                          Test Connection
                        </Button>
                        <Button onClick={saveLLMSettings} disabled={llmSaving}>
                          {llmSaving ? (
                            <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                          ) : null}
                          Save Settings
                        </Button>
                      </div>
                    </>
                  )}
                </CardContent>
              </Card>
            </TabsContent>

            {/* MCP Servers Tab */}
            <TabsContent value="mcp" className="space-y-4">
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center justify-between">
                    <span>MCP Servers</span>
                    <Dialog open={showAddServer} onOpenChange={setShowAddServer}>
                      <DialogTrigger asChild>
                        <Button size="sm">
                          <Plus className="h-4 w-4 mr-2" />
                          Add Server
                        </Button>
                      </DialogTrigger>
                      <DialogContent>
                        <DialogHeader>
                          <DialogTitle>Add MCP Server</DialogTitle>
                          <DialogDescription>
                            Configure a new Model Context Protocol server
                          </DialogDescription>
                        </DialogHeader>
                        <div className="grid gap-4 py-4">
                          <div className="grid gap-2">
                            <Label htmlFor="server-name">Name</Label>
                            <Input
                              id="server-name"
                              value={newServer.name}
                              onChange={(e) => setNewServer(prev => ({ ...prev, name: e.target.value }))}
                              placeholder="My MCP Server"
                            />
                          </div>

                          <div className="grid gap-2">
                            <Label htmlFor="transport-type">Transport Type</Label>
                            <Select
                              value={newServer.transport_type}
                              onValueChange={(value: "stdio" | "sse") => setNewServer(prev => ({ ...prev, transport_type: value }))}
                            >
                              <SelectTrigger>
                                <SelectValue />
                              </SelectTrigger>
                              <SelectContent>
                                <SelectItem value="stdio">stdio (Local process)</SelectItem>
                                <SelectItem value="sse">SSE (Remote server)</SelectItem>
                              </SelectContent>
                            </Select>
                          </div>

                          {newServer.transport_type === "stdio" ? (
                            <>
                              <div className="grid gap-2">
                                <Label htmlFor="command">Command</Label>
                                <Input
                                  id="command"
                                  value={newServer.command}
                                  onChange={(e) => setNewServer(prev => ({ ...prev, command: e.target.value }))}
                                  placeholder="npx"
                                />
                              </div>
                              <div className="grid gap-2">
                                <Label htmlFor="args">Arguments (space-separated)</Label>
                                <Input
                                  id="args"
                                  value={newServer.args}
                                  onChange={(e) => setNewServer(prev => ({ ...prev, args: e.target.value }))}
                                  placeholder="@modelcontextprotocol/server-filesystem"
                                />
                              </div>
                            </>
                          ) : (
                            <div className="grid gap-2">
                              <Label htmlFor="url">Server URL</Label>
                              <Input
                                id="url"
                                value={newServer.url}
                                onChange={(e) => setNewServer(prev => ({ ...prev, url: e.target.value }))}
                                placeholder="http://localhost:3000/sse"
                              />
                            </div>
                          )}

                          <div className="flex items-center space-x-2">
                            <Switch
                              id="enabled"
                              checked={newServer.enabled}
                              onCheckedChange={(checked) => setNewServer(prev => ({ ...prev, enabled: checked }))}
                            />
                            <Label htmlFor="enabled">Enable on startup</Label>
                          </div>
                        </div>
                        <DialogFooter>
                          <Button variant="outline" onClick={() => setShowAddServer(false)}>
                            Cancel
                          </Button>
                          <Button onClick={addMCPServer} disabled={!newServer.name}>
                            Add Server
                          </Button>
                        </DialogFooter>
                      </DialogContent>
                    </Dialog>
                  </CardTitle>
                  <CardDescription>
                    Manage Model Context Protocol servers for extended capabilities
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  {mcpLoading ? (
                    <div className="flex items-center justify-center py-8">
                      <Loader2 className="h-6 w-6 animate-spin" />
                    </div>
                  ) : mcpServers.length === 0 ? (
                    <div className="text-center py-8 text-muted-foreground">
                      <Server className="h-12 w-12 mx-auto mb-4 opacity-50" />
                      <p>No MCP servers configured</p>
                      <p className="text-sm">Add a server to extend Local Mind's capabilities</p>
                    </div>
                  ) : (
                    <div className="space-y-3">
                      {mcpServers.map((server) => (
                        <div
                          key={server.id}
                          className="flex items-center justify-between p-4 rounded-lg border bg-card"
                        >
                          <div className="flex items-center gap-3">
                            <div className={`w-2 h-2 rounded-full ${
                              server.status === "running" ? "bg-green-500" :
                              server.status === "stopped" ? "bg-gray-400" :
                              "bg-red-500"
                            }`} />
                            <div>
                              <p className="font-medium">{server.name}</p>
                              <p className="text-xs text-muted-foreground">
                                {server.transport_type === "stdio" ? server.command : server.url}
                              </p>
                            </div>
                          </div>
                          <div className="flex items-center gap-2">
                            <Badge variant="outline">
                              {server.transport_type}
                            </Badge>
                            {server.status === "running" ? (
                              <Button
                                variant="outline"
                                size="icon"
                                onClick={() => toggleMCPServer(server.id, "stop")}
                              >
                                <Square className="h-4 w-4" />
                              </Button>
                            ) : (
                              <Button
                                variant="outline"
                                size="icon"
                                onClick={() => toggleMCPServer(server.id, "start")}
                              >
                                <Play className="h-4 w-4" />
                              </Button>
                            )}
                            <Button
                              variant="outline"
                              size="icon"
                              onClick={() => deleteMCPServer(server.id)}
                            >
                              <Trash2 className="h-4 w-4" />
                            </Button>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </CardContent>
              </Card>
            </TabsContent>
          </Tabs>
        </div>
      </ScrollArea>
    </div>
  )
}
