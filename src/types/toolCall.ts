export interface ToolCall {
  id: string
  name: string
  arguments: Record<string, unknown>
  status: 'executing' | 'completed' | 'error'
  result?: unknown
  error?: string
}
