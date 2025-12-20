import { useState } from "react"
import { ChevronDown, ChevronRight, Wrench, Check, AlertCircle, Loader2 } from "lucide-react"
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible"
import { cn } from "@/lib/utils"

export interface ToolCallData {
  id: string
  name: string
  arguments: Record<string, unknown>
  result?: unknown
  status: "pending" | "running" | "success" | "error"
}

interface ToolCallDetailsProps {
  toolCalls: ToolCallData[]
  className?: string
}

export function ToolCallDetails({ toolCalls, className }: ToolCallDetailsProps) {
  const [openItems, setOpenItems] = useState<Set<string>>(new Set())

  if (!toolCalls || toolCalls.length === 0) {
    return null
  }

  const toggleItem = (id: string) => {
    const newOpenItems = new Set(openItems)
    if (newOpenItems.has(id)) {
      newOpenItems.delete(id)
    } else {
      newOpenItems.add(id)
    }
    setOpenItems(newOpenItems)
  }

  const getStatusIcon = (status: ToolCallData["status"]) => {
    switch (status) {
      case "pending":
        return <Loader2 className="h-3 w-3 animate-spin text-muted-foreground" />
      case "running":
        return <Loader2 className="h-3 w-3 animate-spin text-blue-500" />
      case "success":
        return <Check className="h-3 w-3 text-green-500" />
      case "error":
        return <AlertCircle className="h-3 w-3 text-red-500" />
    }
  }

  const formatJson = (data: unknown): string => {
    try {
      if (typeof data === "string") {
        // Try to parse if it's a JSON string
        try {
          const parsed = JSON.parse(data)
          return JSON.stringify(parsed, null, 2)
        } catch {
          return data
        }
      }
      return JSON.stringify(data, null, 2)
    } catch {
      return String(data)
    }
  }

  return (
    <div className={cn("mt-2 space-y-1", className)}>
      <div className="flex items-center gap-1.5 text-xs text-muted-foreground mb-1">
        <Wrench className="h-3 w-3" />
        <span>Tools Used ({toolCalls.length})</span>
      </div>

      {toolCalls.map((toolCall) => (
        <Collapsible
          key={toolCall.id}
          open={openItems.has(toolCall.id)}
          onOpenChange={() => toggleItem(toolCall.id)}
        >
          <CollapsibleTrigger className="flex items-center gap-2 w-full p-2 rounded-md bg-muted/50 hover:bg-muted transition-colors text-left">
            {openItems.has(toolCall.id) ? (
              <ChevronDown className="h-3 w-3 text-muted-foreground shrink-0" />
            ) : (
              <ChevronRight className="h-3 w-3 text-muted-foreground shrink-0" />
            )}
            <code className="text-xs font-medium text-foreground">{toolCall.name}</code>
            <div className="ml-auto">
              {getStatusIcon(toolCall.status)}
            </div>
          </CollapsibleTrigger>

          <CollapsibleContent className="mt-1">
            <div className="rounded-md bg-muted/30 p-2 space-y-2 text-xs">
              {/* Arguments */}
              <div>
                <div className="text-muted-foreground mb-1">Arguments:</div>
                <pre className="bg-background/50 p-2 rounded overflow-x-auto font-mono text-[10px] leading-relaxed">
                  {formatJson(toolCall.arguments)}
                </pre>
              </div>

              {/* Result */}
              {toolCall.result !== undefined && (
                <div>
                  <div className="text-muted-foreground mb-1">Result:</div>
                  <pre className={cn(
                    "p-2 rounded overflow-x-auto font-mono text-[10px] leading-relaxed max-h-40 overflow-y-auto",
                    toolCall.status === "error"
                      ? "bg-red-500/10 text-red-600 dark:text-red-400"
                      : "bg-background/50"
                  )}>
                    {formatJson(toolCall.result)}
                  </pre>
                </div>
              )}
            </div>
          </CollapsibleContent>
        </Collapsible>
      ))}
    </div>
  )
}
