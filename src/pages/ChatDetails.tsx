import { useState, useEffect, useRef } from "react"
import { useParams, useLocation } from "react-router-dom"
import { ResizablePanelGroup, ResizablePanel, ResizableHandle } from "@/components/ui/resizable"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Send, FileText, ExternalLink, Loader2, AlertCircle, RefreshCw } from "lucide-react"
import { useHeaderStore } from "@/stores/useHeaderStore"
import { API_BASE_URL, DEFAULT_LLM_MODEL, OLLAMA_BASE_URL } from "@/config/app-config"
import { chatService, type Chat, type Message } from "@/services/chat-service"

interface ChatMessage {
  id: string
  type: 'user' | 'assistant'
  content: string
  timestamp: string
  references?: Reference[]
}

interface Reference {
  id: string
  title: string
  type: 'document' | 'research'
  sources: number
  content: string
  document?: Document
}

interface Document {
  title: string
  sections: DocumentSection[]
}

interface DocumentSection {
  title: string
  content: string
}


export default function ChatDetail() {
  const { chatId } = useParams<{ chatId: string }>()
  const location = useLocation()
  const { setTitle, clearTitle } = useHeaderStore()
  const [selectedReference, setSelectedReference] = useState<Reference | null>(null)
  const [message, setMessage] = useState("")
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [loadingMessage, setLoadingMessage] = useState("")
  const [errorRetryCount, setErrorRetryCount] = useState(0)
  const [currentChat, setCurrentChat] = useState<Chat | null>(null)
  const scrollAreaRef = useRef<HTMLDivElement>(null)
  const scrollAnchorRef = useRef<HTMLDivElement>(null)
  const conversationIdRef = useRef<string>(chatId || "")
  const hasProcessedInitialMessage = useRef(false)

  // Helper function to scroll to bottom
  const scrollToBottom = () => {
    // Use scrollIntoView for more reliable scrolling
    if (scrollAnchorRef.current) {
      scrollAnchorRef.current.scrollIntoView({ behavior: 'smooth', block: 'end' })
    }
  }

  // Set the header title based on chatId
  useEffect(() => {
    if (chatId) {
      const formattedTitle = chatId.replace(/-/g, ' ').replace(/\b\w/g, l => l.toUpperCase())
      setTitle(formattedTitle)
    }

    // Clear title on unmount
    return () => {
      clearTitle()
    }
  }, [chatId, setTitle, clearTitle])

  // Load chat and messages from database
  useEffect(() => {
    const loadChatData = async () => {
      if (!chatId) {
        // If no chatId, we'll create a new chat when the first message is sent
        return
      }

      try {
        // Load chat with messages from the API
        const chat = await chatService.getChat(chatId, true)
        setCurrentChat(chat)
        conversationIdRef.current = chat.id

        // Convert API messages to ChatMessage format
        const loadedMessages: ChatMessage[] = chat.messages.map(msg => ({
          id: msg.id,
          type: msg.role as 'user' | 'assistant',
          content: msg.content,
          timestamp: new Date(msg.created_at).toLocaleTimeString('en-US', {
            hour: 'numeric',
            minute: '2-digit'
          }),
          references: msg.citations ? [{
            id: 'ref-' + msg.id,
            title: 'Document Reference',
            type: 'research' as const,
            sources: msg.citations.length,
            content: 'Citations from documents'
          }] : undefined
        }))

        setMessages(loadedMessages)
      } catch (error) {
        console.error('Failed to load chat:', error)
        // If chat doesn't exist, we'll create it when sending the first message
        if (chatId) {
          conversationIdRef.current = chatId
        }
      }
    }

    loadChatData()
  }, [chatId])

  // Handle initial message from navigation state
  useEffect(() => {
    const initialMessage = location.state?.initialMessage
    if (initialMessage && chatId && !hasProcessedInitialMessage.current && messages.length === 0) {
      hasProcessedInitialMessage.current = true
      // Set the message in the input and trigger send
      setMessage(initialMessage)
      setTimeout(() => {
        handleSendMessage()
      }, 100)
    }
  }, [location.state, chatId, messages.length])

  const handleReferenceClick = (reference: Reference) => {
    setSelectedReference(reference)
  }

  const handleSendMessage = async () => {
    if (message.trim() && !isLoading) {
      const userMessage: ChatMessage = {
        id: `msg-${Date.now()}`,
        type: 'user',
        content: message.trim(),
        timestamp: new Date().toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' }),
      }

      setMessages(prev => [...prev, userMessage])
      setMessage("")
      setIsLoading(true)

      // Create a new chat if we don't have one
      if (!conversationIdRef.current) {
        try {
          const newChat = await chatService.createChat({
            title: message.trim().substring(0, 50)
          })
          conversationIdRef.current = newChat.id
          setCurrentChat(newChat)
          setTitle(newChat.title)
        } catch (error) {
          console.error('Failed to create chat:', error)
        }
      }
      setLoadingMessage("Connecting to AI model...")
      setErrorRetryCount(0)

      // Scroll to bottom when user sends a message
      requestAnimationFrame(scrollToBottom)

      // Create assistant message placeholder
      const assistantMessageId = `msg-${Date.now() + 1}`
      const assistantMessage: ChatMessage = {
        id: assistantMessageId,
        type: 'assistant',
        content: '',
        timestamp: new Date().toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' }),
      }

      setMessages(prev => [...prev, assistantMessage])

      try {
        const MAX_RETRIES = 3
        let retryCount = 0
        let lastError = null

        while (retryCount < MAX_RETRIES) {
          try {
            if (retryCount > 0) {
              setLoadingMessage(`Retrying connection (${retryCount}/${MAX_RETRIES})...`)
              await new Promise(resolve => setTimeout(resolve, 1000 * retryCount))
            }

            const response = await fetch(`${API_BASE_URL}/api/v1/chat/stream`, {
              method: 'POST',
              headers: {
                'Content-Type': 'application/json',
              },
              body: JSON.stringify({
                message: userMessage.content,
                conversation_id: conversationIdRef.current,
                include_citations: false,
                temperature: 0.7,
                max_results: 5
              }),
            })

            if (!response.ok) {
              throw new Error(`Server responded with ${response.status}`)
            }

            setLoadingMessage("Processing your request...")

            const reader = response.body?.getReader()
            const decoder = new TextDecoder()
            let fullResponse = ''
            let hasStartedStreaming = false

            if (reader) {
              while (true) {
                const { done, value } = await reader.read()
                if (done) break

                const chunk = decoder.decode(value)
                const lines = chunk.split('\n')

                for (const line of lines) {
                  if (line.startsWith('data: ')) {
                    try {
                      const data = JSON.parse(line.slice(6))

                      if (data.type === 'content') {
                        if (!hasStartedStreaming) {
                          hasStartedStreaming = true
                          setLoadingMessage("")
                        }
                        fullResponse += data.content
                        setMessages(prev => prev.map(msg =>
                          msg.id === assistantMessageId
                            ? { ...msg, content: fullResponse }
                            : msg
                        ))
                        // Scroll to bottom for each chunk - scrollIntoView handles performance
                        requestAnimationFrame(scrollToBottom)
                      } else if (data.type === 'metadata') {
                        setLoadingMessage("Loading context...")
                        // Handle citations if needed
                        if (data.citations && data.citations.length > 0) {
                          setMessages(prev => prev.map(msg =>
                            msg.id === assistantMessageId
                              ? { ...msg, references: data.citations }
                              : msg
                          ))
                        }
                      } else if (data.type === 'error') {
                        if (data.error.toLowerCase().includes('ollama')) {
                          throw new Error('ollama_connection_failed')
                        }
                        throw new Error(data.error)
                      }
                    } catch (e) {
                      if (e instanceof Error && e.message === 'ollama_connection_failed') {
                        throw e
                      }
                      // Ignore parsing errors for incomplete chunks
                    }
                  }
                }
              }
            }

            // Success - break out of retry loop
            setLoadingMessage("")
            // Final scroll after streaming completes
            requestAnimationFrame(() => {
              requestAnimationFrame(scrollToBottom)
            })
            break

          } catch (error) {
            lastError = error
            retryCount++

            if (retryCount >= MAX_RETRIES) {
              break
            }
          }
        }

        // If we exhausted all retries, show error
        if (retryCount >= MAX_RETRIES && lastError) {
          const errorMessage = lastError instanceof Error ? lastError.message : 'Unknown error'
          let userFriendlyMessage = ''

          if (errorMessage.includes('ollama_connection_failed')) {
            userFriendlyMessage = `Cannot connect to Ollama. Please ensure:\n• Ollama is installed and running\n• The model is downloaded (${DEFAULT_LLM_MODEL})\n• The server is accessible at ${OLLAMA_BASE_URL}`
          } else if (errorMessage.includes('fetch')) {
            userFriendlyMessage = `Cannot connect to the backend server. Please ensure:\n• The backend server is running\n• API is accessible at ${API_BASE_URL}\n• Run: cd backend && python main.py`
          } else {
            userFriendlyMessage = `Connection failed: ${errorMessage}\n\nPlease check:\n• Backend server is running\n• Ollama service is active\n• Network connectivity`
          }

          setMessages(prev => prev.map(msg =>
            msg.id === assistantMessageId
              ? { ...msg, content: userFriendlyMessage }
              : msg
          ))
          setErrorRetryCount(prev => prev + 1)
        }
      } finally {
        setIsLoading(false)
        setLoadingMessage("")
      }
    }
  }

  // Auto-scroll to bottom when new messages arrive or content updates
  useEffect(() => {
    // Use requestAnimationFrame to ensure DOM is updated
    requestAnimationFrame(() => {
      scrollToBottom()
    })
  }, [messages])

  // Also scroll when loading state changes (for when streaming completes)
  useEffect(() => {
    if (!isLoading) {
      // Double RAF to ensure content is fully rendered
      requestAnimationFrame(() => {
        requestAnimationFrame(() => {
          scrollToBottom()
        })
      })
    }
  }, [isLoading])

  return (
    <div className="h-full flex flex-col">
      {/* Main Content Area - takes all available space */}
      <div className="flex-1 overflow-hidden">
        <ResizablePanelGroup direction="horizontal" className="h-full">
          {/* Chat Panel */}
          <ResizablePanel defaultSize={selectedReference ? 50 : 100} minSize={30}>
            <div className="h-full flex flex-col">
              {/* Scrollable Messages */}
              <div className="flex-1 overflow-hidden">
                <ScrollArea className="h-full p-4" ref={scrollAreaRef}>
                  <div className="space-y-6">
                    {messages.map((message) => (
                      <div key={message.id} className="space-y-3">
                        <div className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}>
                          <div className={`max-w-[85%] rounded-2xl px-4 py-3 ${
                            message.type === 'user'
                              ? 'bg-muted text-muted-foreground'
                              : message.content.includes('Cannot connect') || message.content.includes('Connection failed')
                              ? 'bg-destructive/10 border border-destructive/20 text-destructive'
                              : ''
                          }`}>
                            {message.type === 'assistant' && message.content === '' && isLoading ? (
                              <div className="flex items-center gap-2">
                                <Loader2 className="h-3 w-3 animate-spin" />
                                <span className="text-sm">{loadingMessage || "Thinking..."}</span>
                              </div>
                            ) : (
                              <>
                                {message.type === 'assistant' && (message.content.includes('Cannot connect') || message.content.includes('Connection failed')) && (
                                  <div className="flex items-center gap-2 mb-2">
                                    <AlertCircle className="h-4 w-4" />
                                    <span className="font-medium text-sm">Connection Error</span>
                                  </div>
                                )}
                                <p className="text-sm leading-relaxed whitespace-pre-wrap">{message.content}</p>
                                {message.type === 'assistant' && (message.content.includes('Cannot connect') || message.content.includes('Connection failed')) && errorRetryCount < 3 && (
                                  <Button
                                    size="sm"
                                    variant="outline"
                                    className="mt-3 h-7 text-xs"
                                    onClick={() => {
                                      const lastUserMsg = messages.filter(m => m.type === 'user').pop()
                                      if (lastUserMsg) {
                                        setMessage(lastUserMsg.content)
                                        setMessages(prev => prev.slice(0, -2))
                                        setTimeout(() => handleSendMessage(), 100)
                                      }
                                    }}
                                  >
                                    <RefreshCw className="h-3 w-3 mr-1" />
                                    Retry
                                  </Button>
                                )}
                              </>
                            )}
                            <p className="text-xs opacity-70 mt-2">{message.timestamp}</p>
                          </div>
                        </div>

                        {/* References */}
                        {message.references && (
                          <div className="ml-4 space-y-2">
                            {message.references.map((ref) => (
                              <Button
                                key={ref.id}
                                variant="outline"
                                size="sm"
                                className="h-auto p-3 justify-start bg-card hover:bg-accent/50 border-border text-left"
                                onClick={() => handleReferenceClick(ref)}
                              >
                                <div className="flex items-start gap-3 w-full">
                                  <FileText className="h-4 w-4 text-primary mt-0.5 flex-shrink-0" />
                                  <div className="flex-1 min-w-0">
                                    <div className="flex items-center gap-2">
                                      <span className="text-sm font-medium text-foreground">{ref.title}</span>
                                      <ExternalLink className="h-3 w-3 text-muted-foreground" />
                                    </div>
                                    <div className="flex items-center gap-2 mt-1">
                                      <span className="text-xs text-muted-foreground capitalize">{ref.type}</span>
                                      <span className="text-xs text-muted-foreground">•</span>
                                      <span className="text-xs text-muted-foreground">{ref.sources} sources</span>
                                    </div>
                                  </div>
                                </div>
                              </Button>
                            ))}
                          </div>
                        )}
                      </div>
                    ))}
                    {/* Scroll anchor for auto-scrolling */}
                    <div ref={scrollAnchorRef} className="h-1" aria-hidden="true" />
                  </div>
                </ScrollArea>
              </div>

              {/* Message Input */}
              <div className="flex-shrink-0 p-4 border-t border-border bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
                <div className="flex gap-2">
                  <Input
                    value={message}
                    onChange={(e) => setMessage(e.target.value)}
                    placeholder="What's in your mind?"
                    className="flex-1"
                    onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && handleSendMessage()}
                  />
                  <Button onClick={handleSendMessage} size="icon" disabled={isLoading}>
                    {isLoading ? (
                      <Loader2 className="h-4 w-4 animate-spin" />
                    ) : (
                      <Send className="h-4 w-4" />
                    )}
                  </Button>
                </div>
              </div>
            </div>
          </ResizablePanel>

          {/* Document Panel */}
          {selectedReference && (
            <>
              <ResizableHandle withHandle />
              <ResizablePanel defaultSize={50} minSize={30}>
                <div className="h-full flex flex-col bg-background">
                  {/* Document Header */}
                  <div className="flex-shrink-0 p-4 border-b border-border bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
                    <h3 className="text-lg font-semibold text-foreground">
                      {selectedReference.document?.title || selectedReference.title}
                    </h3>
                  </div>

                  {/* Scrollable Document Content */}
                  <div className="flex-1 overflow-hidden">
                    <ScrollArea className="h-full p-6">
                      {selectedReference.document?.sections.map((section, index) => (
                        <div key={index} className="mb-8">
                          <h4 className="text-xl font-semibold text-foreground mb-4">
                            {section.title}
                          </h4>
                          <div className="prose prose-sm dark:prose-invert max-w-none">
                            <p className="text-muted-foreground leading-relaxed whitespace-pre-wrap">
                              {section.content}
                            </p>
                          </div>
                        </div>
                      ))}
                    </ScrollArea>
                  </div>
                </div>
              </ResizablePanel>
            </>
          )}
        </ResizablePanelGroup>
      </div>
    </div>
  )
}