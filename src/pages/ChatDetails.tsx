import { useState, useEffect, useRef } from "react"
import { useParams } from "react-router-dom"
import { ResizablePanelGroup, ResizablePanel, ResizableHandle } from "@/components/ui/resizable"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Send, FileText, ExternalLink, Loader2, AlertCircle, RefreshCw } from "lucide-react"

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

// Mock data
const mockChats: Record<string, ChatMessage[]> = {
  "open-source-rag": [
    {
      id: "1",
      type: "user",
      content: "This is an exciting project! Building an open-source alternative to Hyperlink with those advanced document highlighting and reference features would be incredibly valuable for the community. Let me dive deep into researching every aspect needed to build this from the ground up.",
      timestamp: "2 hours ago",
    },
    {
      id: "2", 
      type: "assistant",
      content: "Your technical plan for building an open-source desktop RAG application is ready. It includes architecture recommendations using Tauri for cross-platform deployment, LanceDB for vector storage, PyMuPDF for document processing with position tracking, and a React-based frontend. The plan features killer capabilities like scalable citations with exact-position highlighting, offline-first operation, hybrid retrieval systems, and comprehensive model management - delivering a 97% smaller bundle than Electron alternatives while maintaining enterprise-grade functionality.",
      timestamp: "2 hours ago",
      references: [
        {
          id: "desktop-rag-research",
          title: "Desktop RAG application research",
          type: "research",
          sources: 481,
          content: "Complete research on desktop RAG applications",
          document: {
            title: "Technical Plan for Building an Open-Source Desktop RAG Application",
            sections: [
              {
                title: "Architecture recommendations for cross-platform offline-first document processing",
                content: "Based on extensive research, the recommended technical stack combines Tauri for the desktop framework, LanceDB for vector storage, PyMuPDF for document processing, and a React-based frontend with advanced document viewing capabilities. This architecture delivers a lightweight (2.5-10MB bundle), performant application that fully supports offline operation while implementing killer features like document reference tracking and exact-position highlighting."
              },
              {
                title: "Executive Summary", 
                content: "This technical plan outlines the development of a desktop RAG application using modern technologies for optimal performance and user experience."
              },
              {
                title: "1. Desktop Application Framework",
                content: "Primary Recommendation: Tauri\n\nKey Advantages:\n• Bundle Size: 2.5-10MB vs Electron's 80-120MB\n• Memory Usage: ~50MB vs Electron's 100MB+\n• Startup Time: <500ms vs Electron's 1-2 seconds\n• Security: Rust-based backend with restricted API access\n• Sidecar Support: Perfect for bundling Nexa SDK and ML inference engines"
              },
              {
                title: "Architecture Implementation",
                content: "The application follows a modern architecture pattern with clear separation of concerns between the frontend React/TypeScript interface and the Rust backend for system operations and document processing."
              }
            ]
          }
        }
      ]
    },
    {
      id: "3",
      type: "user", 
      content: "Perfect, I will go with Tauri shell, Next.js + Shadcn UI, Python Backend (sidecar) -> FastAPI, Document Processing, LanceDB",
      timestamp: "2 hours ago"
    },
    {
      id: "4",
      type: "assistant",
      content: "Based on your specific requirements for a fully offline desktop application, I strongly recommend LanceDB over ChromaDB. Here's a detailed comparison:\n\nLanceDB vs ChromaDB for Your Use Case\n\nLanceDB - Clear Winner for Desktop Apps ✅\n\nKey Advantages:\n1. True Embedded Database: Runs entirely in-process with zero server overhead\n2. File-Based Storage: Simple .lance files on disk - no separate processes\n3. Performance: 100x faster than Parquet, 40-60ms query latency\n4. Lightweight: Minimal memory footprint (~50MB)\n5. Multi-modal Native: Handles text, images, documents without plugins",
      timestamp: "2 hours ago"
    }
  ]
}

export default function ChatDetail() {
  const { chatId } = useParams<{ chatId: string }>()
  const [selectedReference, setSelectedReference] = useState<Reference | null>(null)
  const [message, setMessage] = useState("")
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [loadingMessage, setLoadingMessage] = useState("")
  const [errorRetryCount, setErrorRetryCount] = useState(0)
  const scrollAreaRef = useRef<HTMLDivElement>(null)
  const scrollAnchorRef = useRef<HTMLDivElement>(null)
  const conversationIdRef = useRef<string>(chatId || `chat-${Date.now()}`)

  // Helper function to scroll to bottom
  const scrollToBottom = () => {
    // Use scrollIntoView for more reliable scrolling
    if (scrollAnchorRef.current) {
      scrollAnchorRef.current.scrollIntoView({ behavior: 'smooth', block: 'end' })
    }
  }

  // Load initial messages if they exist
  useEffect(() => {
    if (chatId && mockChats[chatId]) {
      setMessages(mockChats[chatId])
    }
  }, [chatId])

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

            const response = await fetch('http://localhost:52817/api/v1/chat/stream', {
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
            userFriendlyMessage = 'Cannot connect to Ollama. Please ensure:\n• Ollama is installed and running\n• The model is downloaded (gpt-oss:latest)\n• The server is accessible at http://192.168.1.173:11434'
          } else if (errorMessage.includes('fetch')) {
            userFriendlyMessage = 'Cannot connect to the backend server. Please ensure:\n• The backend server is running on port 52817\n• Run: cd backend && python main.py'
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
              {/* Fixed Chat Header */}
              <div className="flex-shrink-0 p-4 border-b border-border bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
                <h2 className="text-lg font-semibold text-foreground">
                  {chatId?.replace(/-/g, ' ').replace(/\b\w/g, l => l.toUpperCase()) || 'Chat'}
                </h2>
              </div>

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