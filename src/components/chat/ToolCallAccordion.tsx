import { useState, memo } from "react"
import { ChevronDown, ChevronRight, Terminal, CheckCircle2, XCircle, ShieldAlert } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { cn } from "@/lib/utils"
import type { ToolCallData } from "@/services/chat-service"

interface ToolCallAccordionProps {
  toolCalls: ToolCallData[]
  onAction?: (toolCallId: string, action: 'approve' | 'deny', toolName: string, toolArgs: any) => void
}

export const ToolCallAccordion = memo(({ toolCalls, onAction }: ToolCallAccordionProps) => {
  const [openItems, setOpenItems] = useState<Record<string, boolean>>({})

  const toggleItem = (id: string) => {
    setOpenItems(prev => ({
      ...prev,
      [id]: !prev[id]
    }))
  }

  if (!toolCalls || toolCalls.length === 0) return null

  return (
    <div className="space-y-2 my-2 w-full max-w-3xl">
      {toolCalls.map(tool => {
        const isOpen = openItems[tool.id] ?? (tool.status === 'executing' || tool.status === 'requires_action')

        return (
          <div key={tool.id} className="border border-border rounded-md overflow-hidden bg-card/50">
            <div
              className={cn(
                "flex items-center gap-2 p-2 px-3 bg-muted/30 cursor-pointer hover:bg-muted/50 transition-colors text-xs select-none",
                tool.status === 'requires_action' && "bg-amber-500/10 border-b border-amber-500/20"
              )}
              onClick={() => toggleItem(tool.id)}
            >
              <div className="text-muted-foreground hover:text-foreground">
                {isOpen ? <ChevronDown className="h-3 w-3" /> : <ChevronRight className="h-3 w-3" />}
              </div>

              <div className="flex items-center gap-1.5 flex-1 overflow-hidden">
                <Terminal className="h-3 w-3 text-muted-foreground flex-shrink-0" />
                <span className="font-medium truncate font-mono text-muted-foreground/80">
                  {tool.name}
                </span>
              </div>

              <div className="flex-shrink-0">
                {tool.status === 'executing' && (
                  <Badge variant="outline" className="h-5 px-1.5 text-[10px] font-normal animate-pulse bg-blue-500/10 text-blue-500 border-blue-500/20 gap-1">
                    <div className="h-1.5 w-1.5 rounded-full bg-blue-500 animate-bounce" />
                    Executing
                  </Badge>
                )}
                {tool.status === 'completed' && (
                  <Badge variant="outline" className="h-5 px-1.5 text-[10px] font-normal bg-green-500/10 text-green-600 border-green-500/20 gap-1">
                    <CheckCircle2 className="h-3 w-3" />
                    {tool.name === 'fetch_url' ? 'Approved' : 'Completed'}
                  </Badge>
                )}
                {tool.status === 'error' && (
                  <Badge variant="outline" className="h-5 px-1.5 text-[10px] font-normal bg-red-500/10 text-red-600 border-red-500/20 gap-1">
                    <XCircle className="h-3 w-3" />
                    {tool.error === 'User denied permission' ? 'Denied' : 'Failed'}
                  </Badge>
                )}
                {tool.status === 'requires_action' && (
                  <Badge variant="outline" className="h-5 px-1.5 text-[10px] font-normal bg-amber-500/10 text-amber-600 border-amber-500/20 gap-1">
                    <ShieldAlert className="h-3 w-3" />
                    Permission Required
                  </Badge>
                )}
              </div>
            </div>

            {isOpen && (
              <div className="border-t border-border/50 bg-background/50 p-3 space-y-3">
                {/* Arguments */}
                <div className="space-y-1">
                  <div className="text-[10px] uppercase text-muted-foreground font-semibold tracking-wider">
                    Details
                  </div>
                  <div className="bg-muted/30 rounded p-2 font-mono text-xs overflow-x-auto whitespace-pre-wrap">
                    {tool.name === 'fetch_url' ? (
                      // Pretty print for fetch_url
                      <div className="flex flex-col gap-1">
                        <span className="text-muted-foreground">URL:</span>
                        <span className="text-primary break-all">{tool.arguments.url as string}</span>
                      </div>
                    ) : (
                      JSON.stringify(tool.arguments, null, 2)
                    )}
                  </div>
                </div>

                {/* Permission UI / Status Label */}
                {(tool.status === 'requires_action' || tool.error === 'User denied permission' || (tool.status === 'completed' && tool.name === 'fetch_url')) && (
                  <div className={cn(
                    "flex items-center justify-end gap-2 p-2 rounded border",
                    tool.status === 'requires_action' ? "bg-amber-500/5 border-amber-500/10" :
                      tool.status === 'completed' ? "bg-green-500/5 border-green-500/10" : "bg-red-500/5 border-red-500/10"
                  )}>
                    <div className={cn(
                      "flex-1 text-xs font-medium flex items-center gap-1.5",
                      tool.status === 'requires_action' ? "text-amber-600/90" :
                        tool.status === 'completed' ? "text-green-600/90" : "text-red-600/90"
                    )}>
                      {tool.status === 'requires_action' && <ShieldAlert className="h-3.5 w-3.5" />}
                      {tool.status === 'completed' && <CheckCircle2 className="h-3.5 w-3.5" />}
                      {tool.error === 'User denied permission' && <XCircle className="h-3.5 w-3.5" />}

                      {tool.status === 'requires_action' ? 'Use web fetch?' :
                        tool.status === 'completed' ? 'Web fetch approved' : 'Web fetch denied'}
                    </div>

                    {tool.status === 'requires_action' && onAction && (
                      <>
                        <Button
                          size="sm"
                          variant="outline"
                          className="h-7 text-xs border-red-200 hover:bg-red-50 hover:text-red-700 dark:border-red-900/50 dark:hover:bg-red-900/20 dark:hover:text-red-400"
                          onClick={(e) => {
                            e.stopPropagation();
                            // Auto-close on deny
                            setOpenItems(prev => ({ ...prev, [tool.id]: false }));
                            onAction(tool.id, 'deny', tool.name, tool.arguments);
                          }}
                        >
                          Deny
                        </Button>
                        <Button
                          size="sm"
                          className="h-7 text-xs bg-amber-600 hover:bg-amber-700 text-white dark:bg-amber-700 dark:hover:bg-amber-600"
                          onClick={(e) => {
                            e.stopPropagation();
                            // Auto-close on approve
                            setOpenItems(prev => ({ ...prev, [tool.id]: false }));
                            onAction(tool.id, 'approve', tool.name, tool.arguments);
                          }}
                        >
                          Allow Web Fetch
                        </Button>
                      </>
                    )}
                  </div>
                )}



                {/* Results */}
                {(tool.result || tool.error) && (
                  <div className="space-y-1">
                    <div className="text-[10px] uppercase text-muted-foreground font-semibold tracking-wider flex items-center justify-between">
                      <span>Result</span>
                    </div>
                    <div className={cn(
                      "rounded p-2 font-mono text-xs overflow-x-auto max-h-[300px]",
                      tool.error ? "bg-red-500/5 text-red-600 dark:text-red-400" : "bg-muted/30"
                    )}>
                      {tool.error ? (
                        tool.error
                      ) : (
                        typeof tool.result === 'string' ? tool.result : JSON.stringify(tool.result, null, 2)
                      )}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        )
      })}
    </div>
  )
});
