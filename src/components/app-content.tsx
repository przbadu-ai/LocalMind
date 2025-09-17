import { useState } from "react"
import { Plus, Search, Code, PenTool, Briefcase, Sparkles, ArrowUp } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"

const actionButtons = [
  { icon: Code, label: "Code", variant: "outline" as const },
  { icon: PenTool, label: "Write", variant: "outline" as const },
  { icon: Briefcase, label: "Career chat", variant: "outline" as const },
]

export function MainContent() {
  const [message, setMessage] = useState("")

  return (
    <main className="flex-1 flex flex-col">
      {/* Welcome Section */}
      <div className="flex-1 flex items-center justify-center p-8">
        <div className="max-w-2xl w-full text-center space-y-8">
          <div className="space-y-4">
            <div className="flex items-center justify-center gap-3">
              <Sparkles className="h-8 w-8 text-primary" />
              <h1 className="text-4xl font-light text-foreground">
                Welcome
              </h1>
            </div>
          </div>

          {/* Input Section */}
          <div className="space-y-4">
            <div className="relative">
              <Input
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                placeholder="How can I help you today?"
                className="w-full h-12 pl-4 pr-12 text-base bg-muted/30 border-border focus:border-primary/50 focus:ring-1 focus:ring-primary/20"
              />
              <div className="absolute right-2 top-1/2 -translate-y-1/2 flex gap-2">
                <Button variant="ghost" size="icon" className="h-8 w-8">
                  <Plus className="h-4 w-4" />
                </Button>
                <Button variant="ghost" size="icon" className="h-8 w-8">
                  <Search className="h-4 w-4" />
                </Button>
              </div>
            </div>

            {/* Action Buttons */}
            <div className="flex flex-wrap justify-center gap-3">
              {actionButtons.map((action, index) => (
                <Button
                  key={index}
                  variant={action.variant}
                  className="h-10 px-4 gap-2 bg-card hover:bg-accent/50 border-border"
                >
                  <action.icon className="h-4 w-4" />
                  {action.label}
                </Button>
              ))}
            </div>

            {/* Version info */}
            <div className="flex items-center justify-center gap-4 text-sm text-muted-foreground pt-4">
              <span className="flex items-center gap-2">
                openai/gpt-oss-20b
                <ArrowUp className="h-3 w-3" />
              </span>
            </div>
          </div>
        </div>
      </div>
    </main>
  )
}