export interface ToolCall {
  id: string
  name: string
  arguments: Record<string, unknown>
  status: 'executing' | 'completed' | 'error' | 'requires_action'
  result?: unknown
  error?: string
}

