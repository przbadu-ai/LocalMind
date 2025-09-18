import { useState } from "react"
import { useParams } from "react-router-dom"
import { ResizablePanelGroup, ResizablePanel, ResizableHandle } from "@/components/ui/resizable"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Send, FileText, ExternalLink } from "lucide-react"

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
  
  const messages = chatId ? mockChats[chatId] || [] : []

  const handleReferenceClick = (reference: Reference) => {
    setSelectedReference(reference)
  }

  const handleSendMessage = () => {
    if (message.trim()) {
      // Handle sending message
      setMessage("")
    }
  }

  return (
    <div className="h-full flex flex-col">
      <ResizablePanelGroup direction="horizontal" className="flex-1">
        {/* Chat Panel */}
        <ResizablePanel defaultSize={selectedReference ? 50 : 100} minSize={30}>
          <div className="h-full flex flex-col">
            {/* Chat Header */}
            <div className="p-4 border-b border-border bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
              <h2 className="text-lg font-semibold text-foreground">
                {chatId?.replace(/-/g, ' ').replace(/\b\w/g, l => l.toUpperCase()) || 'Chat'}
              </h2>
            </div>

            {/* Messages */}
            <ScrollArea className="flex-1 p-4">
              <div className="space-y-6">
                {messages.map((message) => (
                  <div key={message.id} className="space-y-3">
                    <div className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}>
                      <div className={`max-w-[85%] rounded-2xl px-4 py-3 ${
                        message.type === 'user'
                          ? 'bg-primary text-primary-foreground'
                          : 'bg-muted text-muted-foreground'
                      }`}>
                        <p className="text-sm leading-relaxed whitespace-pre-wrap">{message.content}</p>
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
              </div>
            </ScrollArea>

            {/* Message Input */}
            <div className="p-4 border-t border-border bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
              <div className="flex gap-2">
                <Input
                  value={message}
                  onChange={(e) => setMessage(e.target.value)}
                  placeholder="Reply to Claude..."
                  className="flex-1"
                  onKeyPress={(e) => e.key === 'Enter' && handleSendMessage()}
                />
                <Button onClick={handleSendMessage} size="icon">
                  <Send className="h-4 w-4" />
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
                <div className="p-4 border-b border-border bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
                  <h3 className="text-lg font-semibold text-foreground">
                    {selectedReference.document?.title || selectedReference.title}
                  </h3>
                </div>

                {/* Document Content */}
                <ScrollArea className="flex-1 p-6">
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
            </ResizablePanel>
          </>
        )}
      </ResizablePanelGroup>
    </div>
  )
}