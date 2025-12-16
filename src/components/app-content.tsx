import { useState } from "react"
import { Send, Code, PenTool, Sparkles, ArrowUp, Youtube } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { DEFAULT_LLM_MODEL } from "@/config/app-config"
import { useNavigate } from "react-router-dom"
import { chatService } from "@/services/chat-service"

const actionButtons = [
  { icon: Code, label: "Code", variant: "outline" as const },
  { icon: PenTool, label: "Write", variant: "outline" as const },
  { icon: Youtube, label: "YouTube", variant: "outline" as const },
]

export function MainContent() {
  const [message, setMessage] = useState("")
  const [isCreatingChat, setIsCreatingChat] = useState(false)
  const navigate = useNavigate()

  const handleSendMessage = async () => {
    if (message.trim() && !isCreatingChat) {
      setIsCreatingChat(true)
      try {
        // Create a new chat with the message as the title
        const newChat = await chatService.createChat({
          title: message.trim().substring(0, 50)
        })

        // Navigate to the chat detail page with the message in state
        navigate(`/chats/${newChat.id}`, {
          state: { initialMessage: message.trim() }
        })
      } catch (error) {
        console.error('Failed to create chat:', error)
        setIsCreatingChat(false)
      }
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSendMessage()
    }
  }

  return (
    <main className="h-full flex-1 flex flex-col">
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
              <div className="flex items-center gap-2">
                <Input
                  value={message}
                  onChange={(e) => setMessage(e.target.value)}
                  onKeyDown={handleKeyPress}
                  placeholder="How can I help you today?"
                  className="flex-1 h-12 pl-4 pr-4 text-base bg-muted/30 border-border focus:border-primary/50 focus:ring-1 focus:ring-primary/20"
                  disabled={isCreatingChat}
                />
                <Button
                  variant="default"
                  size="icon"
                  className="h-10 w-10"
                  onClick={handleSendMessage}
                  disabled={isCreatingChat || !message.trim()}
                >
                  <Send className="h-4 w-4" />
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
                {DEFAULT_LLM_MODEL}
                <ArrowUp className="h-3 w-3" />
              </span>
            </div>
          </div>
        </div>
      </div>
    </main>
  )
}
