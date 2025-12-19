import { useState, useRef, useEffect } from "react"
import { Send, Code, PenTool, Sparkles, Youtube } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"
import { useNavigate } from "react-router-dom"
import { chatService } from "@/services/chat-service"
import { ModelSelector } from "@/components/ModelSelector"

const actionButtons = [
  { icon: Code, label: "Code", variant: "outline" as const },
  { icon: PenTool, label: "Write", variant: "outline" as const },
  { icon: Youtube, label: "YouTube", variant: "outline" as const },
]

export function MainContent() {
  const [message, setMessage] = useState("")
  const [isCreatingChat, setIsCreatingChat] = useState(false)
  const [selectedProvider, setSelectedProvider] = useState<string | null>(null)
  const [selectedModel, setSelectedModel] = useState<string | null>(null)
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const navigate = useNavigate()

  const handleModelChange = (provider: string, model: string) => {
    setSelectedProvider(provider)
    setSelectedModel(model)
  }

  // Auto-grow textarea
  useEffect(() => {
    const textarea = textareaRef.current
    if (textarea) {
      // Reset height to auto to get the correct scrollHeight
      textarea.style.height = 'auto'
      // Calculate the line height (roughly 24px per line with padding)
      const lineHeight = 24
      const maxLines = 10
      const maxHeight = lineHeight * maxLines
      // Set height based on content, capped at max
      const newHeight = Math.min(textarea.scrollHeight, maxHeight)
      textarea.style.height = `${newHeight}px`
    }
  }, [message])

  const handleSendMessage = async () => {
    if (message.trim() && !isCreatingChat) {
      setIsCreatingChat(true)
      try {
        // Create a new chat with the message as the title and selected model
        const newChat = await chatService.createChat({
          title: message.trim().substring(0, 50),
          model: selectedModel || undefined,
          provider: selectedProvider || undefined,
        })

        // Reset textarea height
        setMessage("")
        if (textareaRef.current) {
          textareaRef.current.style.height = 'auto'
        }

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

          {/* Input Section - Unified container */}
          <div className="space-y-4">
            <div className="border border-border rounded-xl bg-card shadow-sm">
              {/* Textarea area */}
              <div className="p-4">
                <Textarea
                  ref={textareaRef}
                  value={message}
                  onChange={(e) => setMessage(e.target.value)}
                  onKeyDown={handleKeyPress}
                  placeholder="How can I help you today?"
                  className="resize-none border-0 bg-transparent p-0 text-base focus-visible:ring-0 focus-visible:ring-offset-0 shadow-none overflow-hidden"
                  rows={3}
                  disabled={isCreatingChat}
                />
              </div>
              {/* Bottom bar with actions and send button */}
              <div className="flex items-center justify-between px-4 py-3 border-t border-border/50">
                <div className="flex items-center gap-2">
                  {actionButtons.map((action, index) => (
                    <Button
                      key={index}
                      variant="ghost"
                      size="sm"
                      className="h-8 px-3 gap-2 text-muted-foreground hover:text-foreground"
                    >
                      <action.icon className="h-4 w-4" />
                      {action.label}
                    </Button>
                  ))}
                  {/* Divider */}
                  <div className="h-5 w-px bg-border/50 mx-1" />
                  {/* Model selector */}
                  <ModelSelector
                    selectedProvider={selectedProvider}
                    selectedModel={selectedModel}
                    onChange={handleModelChange}
                    disabled={isCreatingChat}
                    compact
                  />
                </div>
                <Button
                  variant="default"
                  size="icon"
                  className="rounded-full h-9 w-9"
                  onClick={handleSendMessage}
                  disabled={isCreatingChat || !message.trim()}
                >
                  <Send className="h-4 w-4" />
                </Button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </main>
  )
}
