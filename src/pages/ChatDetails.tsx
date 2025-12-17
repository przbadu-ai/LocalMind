import { useState, useEffect, useRef, useCallback } from "react"
import { useParams, useLocation } from "react-router-dom"
import { ResizablePanelGroup, ResizablePanel, ResizableHandle } from "@/components/ui/resizable"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Send, Loader2, AlertCircle, RefreshCw, Youtube, X, ExternalLink } from "lucide-react"
import { useHeaderStore } from "@/stores/useHeaderStore"
import { API_BASE_URL, DEFAULT_LLM_MODEL, OLLAMA_BASE_URL } from "@/config/app-config"
import { chatService, type Chat } from "@/services/chat-service"
import { MarkdownRenderer } from "@/components/MarkdownRenderer"
import { YouTubePlayer, TranscriptViewer, type TranscriptSegment } from "@/components/youtube"

interface ChatMessage {
  id: string
  type: 'user' | 'assistant'
  content: string
  timestamp: string
  artifactType?: 'youtube' | 'pdf' | 'image'
  artifactData?: {
    video_id?: string
    url?: string
    transcript_available?: boolean
    error?: string
  }
}

interface TranscriptData {
  video_id: string
  video_url: string
  language_code: string
  is_generated: boolean
  segments: TranscriptSegment[]
  full_text: string
}

export default function ChatDetail() {
  const { chatId } = useParams<{ chatId: string }>()
  const location = useLocation()
  const { setTitle, clearTitle } = useHeaderStore()

  // Chat state
  const [message, setMessage] = useState("")
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [loadingMessage, setLoadingMessage] = useState("")
  const [errorRetryCount, setErrorRetryCount] = useState(0)
  const [currentChat, setCurrentChat] = useState<Chat | null>(null)

  // YouTube state
  const [currentVideoId, setCurrentVideoId] = useState<string | null>(null)
  const [currentTranscript, setCurrentTranscript] = useState<TranscriptData | null>(null)
  const [transcriptError, setTranscriptError] = useState<string | null>(null)
  const [currentPlaybackTime, setCurrentPlaybackTime] = useState(0)
  const [isTranscriptLoading, setIsTranscriptLoading] = useState(false)

  // Refs
  const scrollAreaRef = useRef<HTMLDivElement>(null)
  const scrollAnchorRef = useRef<HTMLDivElement>(null)
  const conversationIdRef = useRef<string>(chatId || "")
  const hasProcessedInitialMessage = useRef(false)
  const chatDataLoaded = useRef(false)

  // Helper function to scroll to bottom
  const scrollToBottom = () => {
    if (scrollAnchorRef.current) {
      scrollAnchorRef.current.scrollIntoView({ behavior: 'smooth', block: 'end' })
    }
  }

  // Set the header title based on chatId
  // Reset state when chatId changes
  useEffect(() => {
    chatDataLoaded.current = false
    setMessages([])
    setCurrentChat(null)
    setTranscriptError(null)
    setCurrentVideoId(null)
    setCurrentTranscript(null)
    setCurrentPlaybackTime(0)

    // If it's a new chat (no ID), we don't need to load anything
    if (!chatId) {
      chatDataLoaded.current = true
    }
  }, [chatId])

  // Clear title on unmount or chatId change
  useEffect(() => {
    return () => {
      clearTitle()
    }
  }, [chatId, clearTitle])

  // Set initial loading state
  useEffect(() => {
    if (chatId && !currentChat) {
      setTitle("Loading...")
    }
  }, [chatId, currentChat, setTitle])

  // Fetch transcript for a video
  const fetchTranscript = useCallback(async (videoId: string) => {
    setIsTranscriptLoading(true)
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/youtube/transcript/${videoId}`)
      const data = await response.json()

      if (data.success && data.transcript) {
        setCurrentTranscript(data.transcript)
        setTranscriptError(null)
      } else {
        setTranscriptError(data.error_help || data.error_message || 'Failed to load transcript')
      }
    } catch (error) {
      setTranscriptError('Failed to fetch transcript')
    } finally {
      setIsTranscriptLoading(false)
    }
  }, [])

  // Load chat and messages from database
  useEffect(() => {
    const loadChatData = async () => {
      // If no chatId, we're in "New Chat" mode, handled by state reset above
      if (!chatId) return

      // If we already loaded this chat ID (and haven't reset), skip
      if (chatDataLoaded.current && conversationIdRef.current === chatId) return

      try {
        const chat = await chatService.getChat(chatId, true)
        setCurrentChat(chat)
        setTitle(chat.title)
        conversationIdRef.current = chat.id
        chatDataLoaded.current = true

        const loadedMessages: ChatMessage[] = chat.messages.map(msg => ({
          id: msg.id,
          type: msg.role as 'user' | 'assistant',
          content: msg.content,
          timestamp: new Date(msg.created_at).toLocaleTimeString('en-US', {
            hour: 'numeric',
            minute: '2-digit'
          }),
          artifactType: msg.artifact_type,
          artifactData: msg.artifact_data,
        }))

        setMessages(loadedMessages)

        // Check for YouTube artifacts in messages and always try to load transcript
        const youtubeMessage = loadedMessages.find(m => m.artifactType === 'youtube' && m.artifactData?.video_id)
        if (youtubeMessage?.artifactData?.video_id) {
          setCurrentVideoId(youtubeMessage.artifactData.video_id)
          // Always try to fetch transcript when loading a YouTube chat
          fetchTranscript(youtubeMessage.artifactData.video_id)
        }
      } catch (error) {
        console.error('Failed to load chat:', error)
        if (chatId) {
          conversationIdRef.current = chatId
        }
      }
    }

    loadChatData()
  }, [chatId, fetchTranscript])

  // Close video panel
  const handleCloseVideo = () => {
    setCurrentVideoId(null)
    setCurrentTranscript(null)
    setTranscriptError(null)
    setCurrentPlaybackTime(0)
  }

  // Send message function that accepts an optional message parameter
  const sendMessage = useCallback(async (messageToSend: string) => {
    if (!messageToSend.trim() || isLoading) return

    const userMessage: ChatMessage = {
      id: `msg-${Date.now()}`,
      type: 'user',
      content: messageToSend.trim(),
      timestamp: new Date().toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' }),
    }

    setMessages(prev => [...prev, userMessage])
    setMessage("")
    setIsLoading(true)

    // Create a new chat if we don't have one
    if (!conversationIdRef.current) {
      try {
        const newChat = await chatService.createChat({
          title: messageToSend.trim().substring(0, 50)
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
              temperature: 0.7,
              include_transcript: true,
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
                      requestAnimationFrame(scrollToBottom)
                    } else if (data.type === 'youtube_detected') {
                      setCurrentVideoId(data.video_id)
                      setLoadingMessage("Fetching video transcript...")
                      // Update user message with artifact data
                      setMessages(prev => prev.map(msg =>
                        msg.id === userMessage.id
                          ? {
                            ...msg,
                            artifactType: 'youtube',
                            artifactData: {
                              video_id: data.video_id,
                              url: data.url,
                            }
                          }
                          : msg
                      ))
                    } else if (data.type === 'transcript_status') {
                      if (data.success) {
                        // Fetch transcript immediately when it's ready
                        fetchTranscript(data.video_id)
                        setMessages(prev => prev.map(msg =>
                          msg.id === userMessage.id && msg.artifactData
                            ? {
                              ...msg,
                              artifactData: {
                                ...msg.artifactData,
                                transcript_available: true,
                              }
                            }
                            : msg
                        ))
                      } else {
                        setTranscriptError(data.error_message || 'Failed to load transcript')
                      }
                      // Don't clear loading message here - wait for LLM response
                    } else if (data.type === 'transcript_loading') {
                      setLoadingMessage("Extracting transcript from YouTube...")
                    } else if (data.type === 'llm_starting') {
                      setLoadingMessage("Generating response...")
                    } else if (data.type === 'done') {
                      // Update conversation ID if new
                      if (data.conversation_id) {
                        conversationIdRef.current = data.conversation_id
                      }
                    } else if (data.type === 'error') {
                      if (data.error.toLowerCase().includes('llm') || data.error.toLowerCase().includes('connection')) {
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
          userFriendlyMessage = `Cannot connect to LLM service. Please ensure:\n• The LLM server is running\n• The model is available (${DEFAULT_LLM_MODEL})\n• The server is accessible at ${OLLAMA_BASE_URL}`
        } else if (errorMessage.includes('fetch')) {
          userFriendlyMessage = `Cannot connect to the backend server. Please ensure:\n• The backend server is running\n• API is accessible at ${API_BASE_URL}\n• Run: cd backend && python -m backend.main`
        } else {
          userFriendlyMessage = `Connection failed: ${errorMessage}\n\nPlease check:\n• Backend server is running\n• LLM service is active\n• Network connectivity`
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
  }, [isLoading, fetchTranscript, setTitle])

  // Wrapper for button click
  const handleSendMessage = useCallback(() => {
    sendMessage(message)
  }, [message, sendMessage])

  // Handle initial message from navigation state
  useEffect(() => {
    const initialMessage = location.state?.initialMessage
    if (initialMessage && chatId && !hasProcessedInitialMessage.current) {
      hasProcessedInitialMessage.current = true
      // Directly send the message without setting state first
      sendMessage(initialMessage)
    }
  }, [location.state, chatId, sendMessage])

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    requestAnimationFrame(() => {
      scrollToBottom()
    })
  }, [messages])

  useEffect(() => {
    if (!isLoading) {
      requestAnimationFrame(() => {
        requestAnimationFrame(() => {
          scrollToBottom()
        })
      })
    }
  }, [isLoading])

  // Determine if we should show two-column layout
  const hasVideoArtifact = currentVideoId !== null

  return (
    <div className="h-full flex flex-col">
      <div className="flex-1 overflow-hidden">
        <ResizablePanelGroup direction="horizontal" className="h-full">
          {/* Chat Panel */}
          <ResizablePanel defaultSize={hasVideoArtifact ? 50 : 100} minSize={30}>
            <div className="h-full flex flex-col">
              {/* Scrollable Messages */}
              <div className="flex-1 overflow-hidden">
                <ScrollArea className="h-full p-4" ref={scrollAreaRef}>
                  <div className="space-y-6">
                    {messages.map((msg) => (
                      <div key={msg.id} className="space-y-3">
                        <div className={`flex ${msg.type === 'user' ? 'justify-end' : 'justify-start'}`}>
                          <div className={`max-w-[85%] rounded-2xl px-4 py-3 ${msg.type === 'user'
                            ? 'bg-muted text-muted-foreground'
                            : msg.content.includes('Cannot connect') || msg.content.includes('Connection failed')
                              ? 'bg-destructive/10 border border-destructive/20 text-destructive'
                              : ''
                            }`}>
                            {msg.type === 'assistant' && msg.content === '' && isLoading ? (
                              <div className="flex items-center gap-2">
                                <Loader2 className="h-3 w-3 animate-spin" />
                                <span className="text-sm">{loadingMessage || "Thinking..."}</span>
                              </div>
                            ) : (
                              <>
                                {msg.type === 'assistant' && (msg.content.includes('Cannot connect') || msg.content.includes('Connection failed')) && (
                                  <div className="flex items-center gap-2 mb-2">
                                    <AlertCircle className="h-4 w-4" />
                                    <span className="font-medium text-sm">Connection Error</span>
                                  </div>
                                )}
                                {msg.type === 'assistant' ? (
                                  <MarkdownRenderer content={msg.content} />
                                ) : (
                                  <p className="text-sm leading-relaxed whitespace-pre-wrap">{msg.content}</p>
                                )}
                                {msg.type === 'assistant' && (msg.content.includes('Cannot connect') || msg.content.includes('Connection failed')) && errorRetryCount < 3 && (
                                  <Button
                                    size="sm"
                                    variant="outline"
                                    className="mt-3 h-7 text-xs"
                                    onClick={() => {
                                      const lastUserMsg = messages.filter(m => m.type === 'user').pop()
                                      if (lastUserMsg) {
                                        setMessages(prev => prev.slice(0, -2))
                                        sendMessage(lastUserMsg.content)
                                      }
                                    }}
                                  >
                                    <RefreshCw className="h-3 w-3 mr-1" />
                                    Retry
                                  </Button>
                                )}
                              </>
                            )}
                            <p className="text-xs opacity-70 mt-2">{msg.timestamp}</p>
                          </div>
                        </div>

                        {/* YouTube artifact indicator */}
                        {msg.artifactType === 'youtube' && msg.artifactData?.video_id && (
                          <div className="ml-4">
                            <Button
                              variant="outline"
                              size="sm"
                              className="h-auto p-3 justify-start bg-card hover:bg-accent/50 border-border text-left"
                              onClick={() => {
                                setCurrentVideoId(msg.artifactData!.video_id!)
                                fetchTranscript(msg.artifactData!.video_id!)
                              }}
                            >
                              <div className="flex items-center gap-3">
                                <Youtube className="h-4 w-4 text-red-500" />
                                <div>
                                  <span className="text-sm font-medium">YouTube Video</span>
                                  <div className="text-xs text-muted-foreground">
                                    {msg.artifactData.transcript_available ? 'Transcript available' : 'Click to load'}
                                  </div>
                                </div>
                              </div>
                            </Button>
                          </div>
                        )}
                      </div>
                    ))}
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
                    placeholder="Send a message or paste a YouTube URL..."
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

          {/* Video/Transcript Panel */}
          {hasVideoArtifact && (
            <>
              <ResizableHandle withHandle />
              <ResizablePanel defaultSize={50} minSize={30}>
                <div className="h-full flex flex-col bg-background">
                  {/* Panel Header */}
                  <div className="flex-shrink-0 p-3 border-b border-border flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Youtube className="h-5 w-5 text-red-500" />
                      <span className="font-medium">YouTube Video</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <Button
                        variant="ghost"
                        size="sm"
                        asChild
                      >
                        <a
                          href={`https://www.youtube.com/watch?v=${currentVideoId}`}
                          target="_blank"
                          rel="noopener noreferrer"
                        >
                          <ExternalLink className="h-4 w-4 mr-1" />
                          Open
                        </a>
                      </Button>
                      <Button
                        variant="ghost"
                        size="icon"
                        className="h-8 w-8"
                        onClick={handleCloseVideo}
                      >
                        <X className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>

                  {/* Video Player */}
                  <div className="flex-shrink-0 p-3">
                    <YouTubePlayer
                      videoId={currentVideoId}
                      onTimeUpdate={setCurrentPlaybackTime}
                    />
                  </div>

                  {/* Transcript Tabs */}
                  <Tabs defaultValue="transcript" className="flex-1 flex flex-col overflow-hidden">
                    <TabsList className="mx-3">
                      <TabsTrigger value="transcript">Transcript</TabsTrigger>
                      <TabsTrigger value="info">Info</TabsTrigger>
                    </TabsList>

                    <TabsContent value="transcript" className="flex-1 overflow-hidden mt-0">
                      {isTranscriptLoading ? (
                        <div className="flex items-center justify-center h-full gap-2">
                          <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
                          <span className="text-sm text-muted-foreground">Loading transcript...</span>
                        </div>
                      ) : currentTranscript ? (
                        <TranscriptViewer
                          segments={currentTranscript.segments}
                          currentTime={currentPlaybackTime}
                        />
                      ) : transcriptError ? (
                        <div className="p-4">
                          <div className="bg-destructive/10 border border-destructive/20 rounded-lg p-4">
                            <div className="flex items-center gap-2 mb-2">
                              <AlertCircle className="h-4 w-4 text-destructive" />
                              <span className="font-medium text-destructive">Transcript Unavailable</span>
                            </div>
                            <p className="text-sm text-muted-foreground whitespace-pre-wrap">
                              {transcriptError}
                            </p>
                          </div>
                        </div>
                      ) : (
                        <div className="flex items-center justify-center h-full">
                          <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
                        </div>
                      )}
                    </TabsContent>

                    <TabsContent value="info" className="flex-1 overflow-hidden mt-0 p-4">
                      {currentTranscript && (
                        <div className="space-y-4">
                          <div className="grid grid-cols-3 gap-4">
                            <div className="bg-muted/50 rounded-lg p-3 text-center">
                              <p className="text-2xl font-bold">
                                {currentTranscript.segments.length}
                              </p>
                              <p className="text-xs text-muted-foreground">Segments</p>
                            </div>
                            <div className="bg-muted/50 rounded-lg p-3 text-center">
                              <p className="text-2xl font-bold">
                                {currentTranscript.language_code.toUpperCase()}
                              </p>
                              <p className="text-xs text-muted-foreground">Language</p>
                            </div>
                            <div className="bg-muted/50 rounded-lg p-3 text-center">
                              <p className="text-2xl font-bold">
                                {currentTranscript.is_generated ? 'Auto' : 'Manual'}
                              </p>
                              <p className="text-xs text-muted-foreground">Type</p>
                            </div>
                          </div>
                          <div>
                            <p className="text-sm text-muted-foreground">
                              Video ID: {currentVideoId}
                            </p>
                          </div>
                        </div>
                      )}
                    </TabsContent>
                  </Tabs>
                </div>
              </ResizablePanel>
            </>
          )}
        </ResizablePanelGroup>
      </div>
    </div>
  )
}
