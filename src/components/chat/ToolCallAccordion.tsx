import { Loader2 } from "lucide-react"
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion"
import { Badge } from "@/components/ui/badge"
import { JsonViewer } from "./JsonViewer"
import type { ToolCall } from "@/types/toolCall"

interface ToolCallAccordionProps {
  toolCalls: ToolCall[]
}

function getStatusBadge(status: ToolCall["status"]) {
  switch (status) {
    case "completed":
      return <Badge variant="success">Completed</Badge>
    case "executing":
      return (
        <Badge variant="warning" className="flex items-center gap-1">
          <Loader2 className="h-3 w-3 animate-spin" />
          Executing
        </Badge>
      )
    case "error":
      return <Badge variant="destructive">Error</Badge>
    default:
      return null
  }
}

export function ToolCallAccordion({ toolCalls }: ToolCallAccordionProps) {
  if (!toolCalls || toolCalls.length === 0) {
    return null
  }

  return (
    <div className="space-y-2 mb-4">
      {toolCalls.map((toolCall) => (
        <Accordion
          key={toolCall.id}
          type="single"
          collapsible
          className="border rounded-lg bg-muted/50"
        >
          <AccordionItem value={toolCall.id} className="border-0">
            <AccordionTrigger className="px-4 py-3 hover:no-underline">
              <div className="flex items-center justify-between w-full pr-2">
                <span className="font-medium text-sm">{toolCall.name}</span>
                {getStatusBadge(toolCall.status)}
              </div>
            </AccordionTrigger>
            <AccordionContent className="px-4 pb-4">
              <div className="space-y-4">
                <JsonViewer data={toolCall.arguments} label="Arguments:" />
                {toolCall.status === "completed" && toolCall.result !== undefined && (
                  <JsonViewer data={toolCall.result} label="Output:" />
                )}
                {toolCall.status === "error" && toolCall.error && (
                  <div className="text-sm text-destructive">
                    Error: {toolCall.error}
                  </div>
                )}
              </div>
            </AccordionContent>
          </AccordionItem>
        </Accordion>
      ))}
    </div>
  )
}
