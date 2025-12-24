import { useState, useEffect, useRef, useCallback } from "react"
import { useParams, useLocation } from "react-router-dom"
import { ResizablePanelGroup, ResizablePanel, ResizableHandle } from "@/components/ui/resizable"
import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Send, Loader2, AlertCircle, RefreshCw, Youtube, X, ExternalLink, Square, Brain, Zap, Hash, Clock, Copy, Check, FileText } from "lucide-react"
import { Badge } from "@/components/ui/badge"
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetDescription } from "@/components/ui/sheet"
import { Dialog, DialogContent } from "@/components/ui/dialog"
import { useIsMobile } from "@/hooks/use-mobile"
import { useHeaderStore } from "@/stores/useHeaderStore"
import { API_BASE_URL, OLLAMA_BASE_URL } from "@/config/app-config"
import { chatService, type Chat } from "@/services/chat-service"
import { MarkdownRenderer } from "@/components/MarkdownRenderer"
import { YouTubePlayer, TranscriptViewer, type TranscriptSegment } from "@/components/youtube"
import { ModelSelector } from "@/components/ModelSelector"
import { ToolCallAccordion } from "@/components/chat/ToolCallAccordion"
import {
  ImageAttachment,
  ImagePreviewList,
  useImagePaste,
  type AttachedImage,
} from "@/components/chat/ImageAttachment"
import {
  DocumentAttachment,
  DocumentPreviewList,
  type AttachedDocument,
  formatFileSize,
} from "@/components/chat/DocumentAttachment"
import { DocumentViewer } from "@/components/chat/DocumentViewer"
import { documentService } from "@/services/document-service"
import type { ToolCall } from "@/types/toolCall"

interface GenerationMetrics {
  prompt_tokens?: number
  completion_tokens?: number
  total_tokens?: number
  prompt_eval_duration?: number
  eval_duration?: number
  total_duration?: number
  tokens_per_second?: number
}

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
    images?: Array<{ data: string; mimeType: string; preview?: string }>
    documents?: Array<{ id: string; name: string; size: number }>
  }
  toolCalls?: ToolCall[]
  metrics?: GenerationMetrics
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

  // Tool execution state
  const [abortController, setAbortController] = useState<AbortController | null>(null)
  const [isExecutingTools, setIsExecutingTools] = useState(false)
  const [currentStreamId, setCurrentStreamId] = useState<string | null>(null)

  // Model state - derived from chat or user selection
  const [chatProvider, setChatProvider] = useState<string | null>(null)
  const [chatModel, setChatModel] = useState<string | null>(null)

  // YouTube state
  const [currentVideoId, setCurrentVideoId] = useState<string | null>(null)
  const [currentTranscript, setCurrentTranscript] = useState<TranscriptData | null>(null)
  const [transcriptError, setTranscriptError] = useState<string | null>(null)
  const [currentPlaybackTime, setCurrentPlaybackTime] = useState(0)
  const [isTranscriptLoading, setIsTranscriptLoading] = useState(false)
  const [isVideoSheetOpen, setIsVideoSheetOpen] = useState(false)
  const isMobile = useIsMobile()

  // Document state
  const [currentDocumentId, setCurrentDocumentId] = useState<string | null>(null)
  const [isDocumentSheetOpen, setIsDocumentSheetOpen] = useState(false)

  // Image attachment state
  const [attachedImages, setAttachedImages] = useState<AttachedImage[]>([])
  // Document attachment state
  const [attachedDocuments, setAttachedDocuments] = useState<AttachedDocument[]>([])
  // Image preview state for maximized view
  const [previewImage, setPreviewImage] = useState<{ src: string; alt?: string } | null>(null)
  // Thinking/reasoning toggle (for models like deepseek-r1, qwen3)
  const [thinkingEnabled, setThinkingEnabled] = useState(true)
  // Add a local state for wider "compact" view support (e.g. tablets or narrow desktop windows)
  const [isCompact, setIsCompact] = useState(false)
  // Track which message was just copied (for copy button feedback)
  const [copiedMessageId, setCopiedMessageId] = useState<string | null>(null)

  useEffect(() => {
    const checkCompact = () => {
      setIsCompact(window.innerWidth < 1024) // Switch to stacked view below 1024px
    }

    // Initial check
    checkCompact()

    window.addEventListener('resize', checkCompact)
    return () => window.removeEventListener('resize', checkCompact)
  }, [])

  // Use effective layout mode
  const showStackedView = isMobile || isCompact

  // Refs
  const scrollAreaRef = useRef<HTMLDivElement>(null)
  const scrollAnchorRef = useRef<HTMLDivElement>(null)
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const messageInputContainerRef = useRef<HTMLDivElement>(null)
  const conversationIdRef = useRef<string>(chatId || "")
  const hasProcessedInitialMessage = useRef(false)
  const chatDataLoaded = useRef(false)
  const isSubmittingRef = useRef(false) // Guard against double submission

  // Image attachment handlers
  const handleAddImage = useCallback((image: AttachedImage) => {
    setAttachedImages(prev => [...prev, image])
  }, [])

  const handleRemoveImage = useCallback((id: string) => {
    setAttachedImages(prev => prev.filter(img => img.id !== id))
  }, [])

  // Document attachment handlers
  const handleAddDocument = useCallback((doc: AttachedDocument) => {
    setAttachedDocuments(prev => [...prev, doc])
  }, [])

  const handleUpdateDocument = useCallback((id: string, updates: Partial<AttachedDocument>) => {
    console.log('[ChatDetails] handleUpdateDocument called:', id, updates)
    setAttachedDocuments(prev => {
      const updated = prev.map(doc =>
        doc.id === id ? { ...doc, ...updates } : doc
      )
      console.log('[ChatDetails] Documents after update:', updated)
      return updated
    })
  }, [])

  const handleRemoveDocument = useCallback(async (id: string) => {
    const doc = attachedDocuments.find(d => d.id === id)
    // If the document was already uploaded, delete it from the server
    if (doc?.document?.id) {
      try {
        await documentService.deleteDocument(doc.document.id)
      } catch (error) {
        console.error('Failed to delete document from server:', error)
      }
    }
    setAttachedDocuments(prev => prev.filter(d => d.id !== id))
  }, [attachedDocuments])

  // Ensure a chat exists for document upload (creates one if needed)
  // This is a fallback - normally the draft chat is created when entering new chat screen
  const ensureChatIdForDocument = useCallback(async (): Promise<string> => {
    if (conversationIdRef.current) {
      return conversationIdRef.current
    }

    // Create a new chat (fallback if draft wasn't created)
    const newChat = await chatService.createChat({
      title: 'New Chat'
    })
    conversationIdRef.current = newChat.id
    setCurrentChat(newChat)
    // Don't notify sidebar yet - wait for first message

    return newChat.id
  }, [])

  // Handle paste events for images
  const handleImagePaste = useImagePaste(handleAddImage, {
    enabled: !isLoading,
    maxImages: 5,
    currentCount: attachedImages.length,
  })

  // Attach paste listener to the message input container
  useEffect(() => {
    const container = messageInputContainerRef.current
    if (!container) return

    const onPaste = (e: Event) => {
      handleImagePaste(e as ClipboardEvent)
    }

    container.addEventListener('paste', onPaste)
    return () => container.removeEventListener('paste', onPaste)
  }, [handleImagePaste])

  // Auto-grow textarea
  useEffect(() => {
    const textarea = textareaRef.current
    if (textarea) {
      // Calculate the line height (roughly 24px per line with padding)
      const lineHeight = 24
      const minHeight = lineHeight // 1 row minimum
      const maxLines = 5
      const maxHeight = lineHeight * maxLines

      // Reset height to measure content
      textarea.style.height = `${minHeight}px`

      // Only grow if content exceeds minimum
      if (textarea.scrollHeight > minHeight) {
        const newHeight = Math.min(textarea.scrollHeight, maxHeight)
        textarea.style.height = `${newHeight}px`
      }
    }
  }, [message])

  // Helper function to scroll to bottom
  const scrollToBottom = () => {
    if (scrollAnchorRef.current) {
      scrollAnchorRef.current.scrollIntoView({ behavior: 'smooth', block: 'end' })
    }
  }

  // Reset state when chatId changes
  useEffect(() => {
    // If we're just navigating to the ID of the chat we just created, don't reset!
    if (chatId && conversationIdRef.current === chatId && messages.length > 0) {
      chatDataLoaded.current = true
      return
    }

    chatDataLoaded.current = false
    hasProcessedInitialMessage.current = false
    conversationIdRef.current = chatId || ""
    setMessages([])
    setCurrentChat(null)
    setTranscriptError(null)
    setTranscriptError(null)
    setCurrentVideoId(null)
    setCurrentTranscript(null)
    setCurrentPlaybackTime(0)
    // Reset document state
    setCurrentDocumentId(null)
    setIsDocumentSheetOpen(false)
    setIsLoading(false)
    setLoadingMessage("")
    setAttachedImages([])
    setAttachedDocuments([])

    // If it's a new chat (no ID), create a draft chat immediately
    // This allows document uploads before the first message is sent
    if (!chatId) {
      chatDataLoaded.current = true

      // Create a draft chat for document uploads
      const createDraftChat = async () => {
        try {
          const newChat = await chatService.createChat({
            title: 'New Chat'
          })
          conversationIdRef.current = newChat.id
          setCurrentChat(newChat)
          // Don't update the title in the header - keep it as "New Chat"
          // Don't notify sidebar yet - wait for first message
        } catch (error) {
          console.error('Failed to create draft chat:', error)
        }
      }
      createDraftChat()
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

        // Set model state from loaded chat
        if (chat.provider) setChatProvider(chat.provider)
        if (chat.model) setChatModel(chat.model)

        // If we have an initial message from navigation (New Chat flow),
        // don't overwrite the messages state as sendMessage() is handling it optimistically.
        // The server won't have the messages yet.
        if (location.state?.initialMessage) {
          return
        }

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
          toolCalls: msg.tool_calls,
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
    setIsVideoSheetOpen(false)
  }

  // Close document panel
  const handleCloseDocument = () => {
    setCurrentDocumentId(null)
    setIsDocumentSheetOpen(false)
  }

  // Open document panel
  const handleOpenDocument = useCallback((documentId: string) => {
    setCurrentDocumentId(documentId)
    if (showStackedView) {
      setIsDocumentSheetOpen(true)
    }
  }, [showStackedView])

  // Send message function that accepts an optional message parameter and optional images/docs
  const sendMessage = useCallback(async (messageToSend: string, imagesOverride?: AttachedImage[], documentsOverride?: AttachedDocument[]) => {
    // Use override images/docs if provided, otherwise use state
    const imagesToUse = imagesOverride ?? attachedImages
    const documentsToUse = documentsOverride ?? attachedDocuments
    // Allow sending if there's text OR if there are attached images/docs
    const hasAttachments = imagesToUse.length > 0 || documentsToUse.length > 0
    if ((!messageToSend.trim() && !hasAttachments) || isLoading || isSubmittingRef.current) return
    isSubmittingRef.current = true

    // Capture current images and documents before clearing
    const imagesToSend = [...imagesToUse]
    const documentsToSend = [...documentsToUse]

    // Use a default message if only images/docs are attached
    const messageContent = messageToSend.trim() ||
      (imagesToSend.length > 0 ? "What's in this image?" :
        documentsToSend.length > 0 ? "What is in this document?" : "")

    const userMessage: ChatMessage = {
      id: `msg-${Date.now()}`,
      type: 'user',
      content: messageContent,
      timestamp: new Date().toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' }),
      // Include images if attached
      ...(imagesToSend.length > 0 && {
        artifactType: 'image' as const,
        artifactData: {
          images: imagesToSend.map(img => ({
            data: img.data,
            mimeType: img.mimeType,
            preview: img.preview,
          })),
        },
      }),
      // Include documents if attached
      ...(documentsToSend.length > 0 && {
        artifactType: 'pdf' as const,
        artifactData: {
          documents: documentsToSend
            .filter(doc => doc.status === 'completed' && doc.document)
            .map(doc => ({
              id: doc.document!.id,
              name: doc.name,
              size: doc.size,
            })),
        },
      }),
    }

    setMessages(prev => [...prev, userMessage])
    setMessage("")
    setAttachedImages([]) // Clear images after capturing
    setAttachedDocuments([]) // Clear documents after capturing
    // Reset textarea height
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
    }
    setIsLoading(true)

    // Track if this is the first message (for sidebar notification)
    const isFirstMessage = messages.length === 0

    // Create a new chat if we don't have one (fallback, normally draft is created)
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

    // Notify sidebar on first message so the chat appears in the list
    if (isFirstMessage) {
      window.dispatchEvent(new Event('chats-updated'))
    }

    setLoadingMessage("Connecting to AI model...")
    setErrorRetryCount(0)
    requestAnimationFrame(scrollToBottom)

    // Create assistant message placeholder with toolCalls initialized
    const assistantMessageId = `msg-${Date.now() + 1}`
    const assistantMessage: ChatMessage = {
      id: assistantMessageId,
      type: 'assistant',
      content: '',
      timestamp: new Date().toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' }),
      toolCalls: [], // Initialize empty toolCalls array for tool call updates
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

          // Create abort controller for this request
          const controller = new AbortController()
          setAbortController(controller)

          // Generate a unique stream ID for cancellation
          const streamId = `stream-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
          setCurrentStreamId(streamId)

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
              stream_id: streamId,
              think: thinkingEnabled,  // Enable thinking/reasoning for supported models
              // Include images if any were attached
              ...(imagesToSend.length > 0 && {
                images: imagesToSend.map(img => ({
                  data: img.data,
                  mime_type: img.mimeType,
                })),
              }),
              // Include documents if any were attached
              ...(userMessage.artifactData?.documents && {
                documents: userMessage.artifactData.documents,
              }),
            }),
            signal: controller.signal,
          })

          if (!response.ok) {
            throw new Error(`Server responded with ${response.status}`)
          }

          setLoadingMessage("Processing your request...")

          const reader = response.body?.getReader()
          const decoder = new TextDecoder()
          let fullResponse = ''
          let fullThinking = ''  // Accumulate thinking/reasoning content separately
          let hasStartedStreaming = false

          // Helper to build the combined message content
          const buildMessageContent = () => {
            // Wrap thinking in <think> tags so MarkdownRenderer displays it in a collapsible section
            if (fullThinking) {
              return `<think>${fullThinking}</think>\n\n${fullResponse}`
            }
            return fullResponse
          }

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

                    if (data.type === 'thinking') {
                      // Handle thinking/reasoning content from models like deepseek-r1, qwen3
                      if (!hasStartedStreaming) {
                        hasStartedStreaming = true
                        setLoadingMessage("Thinking...")
                      }
                      fullThinking += data.content
                      setMessages(prev => {
                        const existingAssistant = prev.find(m => m.id === assistantMessageId)
                        if (existingAssistant) {
                          return prev.map(msg =>
                            msg.id === assistantMessageId
                              ? { ...msg, content: buildMessageContent() }
                              : msg
                          )
                        }
                        return prev
                      })
                      requestAnimationFrame(scrollToBottom)
                    } else if (data.type === 'content') {
                      if (!hasStartedStreaming) {
                        hasStartedStreaming = true
                        setLoadingMessage("")
                      } else if (fullThinking && !fullResponse) {
                        // Transitioning from thinking to content
                        setLoadingMessage("")
                      }
                      fullResponse += data.content
                      setMessages(prev => {
                        // Find or create the assistant message, preserving any existing toolCalls
                        const existingAssistant = prev.find(m => m.id === assistantMessageId)

                        if (existingAssistant) {
                          // Update existing message, preserving toolCalls
                          return prev.map(msg =>
                            msg.id === assistantMessageId
                              ? { ...msg, content: buildMessageContent() }
                              : msg
                          )
                        } else {
                          // Need to add messages - this shouldn't normally happen
                          // as assistantMessage is added before streaming starts
                          let messages = prev
                          if (!prev.some(m => m.id === userMessage.id)) {
                            messages = [...messages, userMessage]
                          }
                          return [...messages, { ...assistantMessage, content: buildMessageContent() }]
                        }
                      })
                      requestAnimationFrame(scrollToBottom)
                    } else if (data.type === 'youtube_detected') {
                      setCurrentVideoId(data.video_id)
                      setLoadingMessage("Fetching video transcript...")
                      // Update user message with artifact data
                      setMessages(prev => prev.map(msg =>
                        msg.id === userMessage.id
                          ? {
                            ...msg,
                            artifactType: 'youtube' as const,
                            artifactData: {
                              video_id: data.video_id,
                              url: data.url,
                              transcript_available: false,
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
                    } else if (data.type === 'tool_call') {
                      // Add tool call to current assistant message
                      setIsExecutingTools(true)
                      setLoadingMessage(`Executing ${data.tool_name}...`)

                      const newToolCall = {
                        id: data.tool_call_id,
                        name: data.tool_name,
                        arguments: data.tool_args || {},
                        status: 'executing' as const,
                      }

                      setMessages(prev => {
                        // Find or create the assistant message
                        const existingAssistant = prev.find(m => m.id === assistantMessageId)

                        if (existingAssistant) {
                          // Update existing message with new tool call
                          return prev.map(msg =>
                            msg.id === assistantMessageId
                              ? {
                                ...msg,
                                toolCalls: [...(msg.toolCalls || []), newToolCall]
                              }
                              : msg
                          )
                        } else {
                          // Need to add both user and assistant messages
                          let messages = prev
                          if (!prev.some(m => m.id === userMessage.id)) {
                            messages = [...messages, userMessage]
                          }
                          // Add assistant message with the tool call already included
                          return [...messages, {
                            ...assistantMessage,
                            toolCalls: [newToolCall]
                          }]
                        }
                      })
                      requestAnimationFrame(scrollToBottom)
                    } else if (data.type === 'tool_result') {
                      // Update tool call with result
                      setMessages(prev => {
                        const existingAssistant = prev.find(m => m.id === assistantMessageId)

                        if (existingAssistant) {
                          return prev.map(msg =>
                            msg.id === assistantMessageId
                              ? {
                                ...msg,
                                toolCalls: msg.toolCalls?.map(tc =>
                                  tc.id === data.tool_call_id
                                    ? {
                                      ...tc,
                                      status: data.error ? 'error' as const : 'completed' as const,
                                      result: data.result,
                                      error: data.error,
                                    }
                                    : tc
                                )
                              }
                              : msg
                          )
                        } else {
                          // This shouldn't happen, but handle gracefully
                          let messages = prev
                          if (!prev.some(m => m.id === userMessage.id)) {
                            messages = [...messages, userMessage]
                          }
                          return [...messages, assistantMessage]
                        }
                      })
                      setIsExecutingTools(false)
                      setLoadingMessage("Generating response...")
                      requestAnimationFrame(scrollToBottom)
                    } else if (data.type === 'done') {
                      // Update conversation ID if new
                      if (data.conversation_id) {
                        conversationIdRef.current = data.conversation_id
                      }
                      // Update title if provided (generated by LLM)
                      if (data.title) {
                        setTitle(data.title)
                        setCurrentChat(prev => prev ? { ...prev, title: data.title } : prev)
                        window.dispatchEvent(new Event('chats-updated'))
                      }
                      // Store generation metrics on the assistant message
                      if (data.metrics) {
                        setMessages(prev => prev.map(msg =>
                          msg.id === assistantMessageId
                            ? { ...msg, metrics: data.metrics }
                            : msg
                        ))
                      }
                    } else if (data.type === 'cancelled') {
                      // Stream was cancelled by user - update any executing tools
                      setMessages(prev => prev.map(msg =>
                        msg.id === assistantMessageId && msg.toolCalls
                          ? {
                            ...msg,
                            toolCalls: msg.toolCalls.map(tc =>
                              tc.status === 'executing'
                                ? { ...tc, status: 'error' as const, error: 'Stopped by user' }
                                : tc
                            )
                          }
                          : msg
                      ))
                      setIsExecutingTools(false)
                      setCurrentStreamId(null)
                      setIsLoading(false)
                      setLoadingMessage("")
                      isSubmittingRef.current = false
                      return
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
          setIsExecutingTools(false)
          setAbortController(null)
          setCurrentStreamId(null)
          requestAnimationFrame(() => {
            requestAnimationFrame(scrollToBottom)
          })
          break

        } catch (error) {
          // Handle user abort
          if (error instanceof Error && error.name === 'AbortError') {
            // User cancelled - update executing tool calls to show stopped
            setMessages(prev => prev.map(msg =>
              msg.id === assistantMessageId && msg.toolCalls
                ? {
                  ...msg,
                  toolCalls: msg.toolCalls.map(tc =>
                    tc.status === 'executing'
                      ? { ...tc, status: 'error' as const, error: 'Stopped by user' }
                      : tc
                  )
                }
                : msg
            ))
            setIsExecutingTools(false)
            setAbortController(null)
            setIsLoading(false)
            setLoadingMessage("")
            isSubmittingRef.current = false
            return // Exit the function entirely, don't retry
          }

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
          const modelInfo = chatModel || 'selected model'
          userFriendlyMessage = `Cannot connect to LLM service. Please ensure:\n• The LLM server is running\n• The model is available (${modelInfo})\n• The server is accessible at ${OLLAMA_BASE_URL}`
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
      isSubmittingRef.current = false // Reset submission guard
    }
  }, [isLoading, fetchTranscript, setTitle, attachedImages, attachedDocuments, thinkingEnabled])

  // Wrapper for button click
  const handleSendMessage = useCallback(() => {
    sendMessage(message)
  }, [message, sendMessage])

  // Handle model change - update chat in database
  const handleModelChange = useCallback(async (provider: string, model: string) => {
    setChatProvider(provider)
    setChatModel(model)

    // If we have a chat ID, persist the model change to the database
    if (chatId) {
      try {
        await chatService.updateChatModel(chatId, provider, model)
      } catch (error) {
        console.error('Failed to update chat model:', error)
      }
    }
  }, [chatId])

  // Handle initial message from navigation state
  useEffect(() => {
    const initialMessage = location.state?.initialMessage
    const initialImages = location.state?.initialImages as AttachedImage[] | undefined
    const initialDocuments = location.state?.initialDocuments as AttachedDocument[] | undefined

    if (initialMessage && chatId && !hasProcessedInitialMessage.current) {
      hasProcessedInitialMessage.current = true
      // Set images in state for UI consistency
      if (initialImages && initialImages.length > 0) {
        setAttachedImages(initialImages)
      }
      // Set documents in state for UI consistency
      if (initialDocuments && initialDocuments.length > 0) {
        setAttachedDocuments(initialDocuments)
      }
      // Pass both directly to sendMessage to avoid async state issues
      sendMessage(initialMessage, initialImages, initialDocuments)
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
  const hasDocumentArtifact = currentDocumentId !== null
  const hasSidePanel = hasVideoArtifact || hasDocumentArtifact

  // Ensure video sheet is open when switching to mobile with active video
  useEffect(() => {
    if (showStackedView && hasVideoArtifact && !isVideoSheetOpen) {
      // Optional: auto-open if needed, or leave it to user
      // setIsVideoSheetOpen(true)
    }
    if (showStackedView && hasDocumentArtifact && !isDocumentSheetOpen) {
      // Optional: auto-open if needed
    }
  }, [showStackedView, hasVideoArtifact, isVideoSheetOpen, hasDocumentArtifact, isDocumentSheetOpen])

  const ChatPanel = (
    <div className="h-full flex flex-col">
      {/* Scrollable Messages */}
      <div className="flex-1 overflow-hidden">
        <ScrollArea className="h-full p-4" ref={scrollAreaRef}>
          <div className="space-y-6">
            {messages.map((msg) => (
              <div key={msg.id} className="space-y-3">
                {/* Tool calls appear ABOVE assistant message content */}
                {msg.type === 'assistant' && msg.toolCalls && msg.toolCalls.length > 0 && (
                  <ToolCallAccordion toolCalls={msg.toolCalls} />
                )}
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
                          <>
                            {/* Show attached images in user message */}
                            {msg.artifactType === 'image' && msg.artifactData?.images && (
                              <div className="flex flex-wrap gap-2 mb-2">
                                {msg.artifactData.images.map((img, idx) => (
                                  <img
                                    key={idx}
                                    src={img.preview || `data:${img.mimeType};base64,${img.data}`}
                                    alt={`Attached image ${idx + 1}`}
                                    className="max-w-[200px] max-h-[200px] rounded-lg object-cover cursor-zoom-in hover:opacity-90 transition-opacity active:scale-[0.98]"
                                    onClick={() => setPreviewImage({
                                      src: img.preview || `data:${img.mimeType};base64,${img.data}`,
                                      alt: `Attached image ${idx + 1}`
                                    })}
                                  />
                                ))}
                              </div>
                            )}
                            <p className="text-sm leading-relaxed whitespace-pre-wrap">{msg.content}</p>
                          </>
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
                    <div className="flex items-center flex-wrap gap-2 mt-2">
                      <span className="text-xs opacity-70">{msg.timestamp}</span>
                      {msg.type === 'assistant' && msg.metrics && (
                        <div className="flex items-center flex-wrap gap-1.5">
                          {msg.metrics.tokens_per_second && (
                            <Badge variant="secondary" className="h-5 px-1.5 text-[10px] font-normal gap-1">
                              <Zap className="h-3 w-3" />
                              {msg.metrics.tokens_per_second.toFixed(1)} tok/s
                            </Badge>
                          )}
                          {msg.metrics.completion_tokens && (
                            <Badge variant="outline" className="h-5 px-1.5 text-[10px] font-normal gap-1">
                              <Hash className="h-3 w-3" />
                              {msg.metrics.completion_tokens} tokens
                            </Badge>
                          )}
                          {msg.metrics.total_duration && (
                            <Badge variant="outline" className="h-5 px-1.5 text-[10px] font-normal gap-1">
                              <Clock className="h-3 w-3" />
                              {msg.metrics.total_duration.toFixed(1)}s
                            </Badge>
                          )}
                        </div>
                      )}
                      {/* Copy button for assistant messages */}
                      {msg.type === 'assistant' && msg.content && (
                        <button
                          onClick={async () => {
                            await navigator.clipboard.writeText(msg.content)
                            setCopiedMessageId(msg.id)
                            setTimeout(() => setCopiedMessageId(null), 3000)
                          }}
                          className="flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground transition-colors ml-1"
                          title="Copy response as markdown"
                        >
                          {copiedMessageId === msg.id ? (
                            <>
                              <Check className="h-3 w-3 text-green-500" />
                              <span className="text-green-500">Copied!</span>
                            </>
                          ) : (
                            <>
                              <Copy className="h-3 w-3" />
                              <span>Copy</span>
                            </>
                          )}
                        </button>
                      )}
                    </div>
                  </div>
                </div>

                {/* YouTube artifact indicator */}
                {msg.artifactType === 'youtube' && msg.artifactData?.video_id && (
                  <div className={`flex ${msg.type === 'user' ? 'justify-end' : 'justify-start'} ml-4 mr-4 mb-2`}>
                    <Button
                      variant="outline"
                      size="sm"
                      className="h-auto p-3 justify-start bg-card hover:bg-accent/50 border-border text-left"
                      onClick={() => {
                        handleCloseDocument() // Close document if open
                        setCurrentVideoId(msg.artifactData!.video_id!)
                        fetchTranscript(msg.artifactData!.video_id!)
                        if (showStackedView) setIsVideoSheetOpen(true)
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

                {/* PDF artifact indicator */}
                {msg.artifactType === 'pdf' && msg.artifactData?.documents && msg.artifactData.documents.length > 0 && (
                  <div className={`flex ${msg.type === 'user' ? 'justify-end' : 'justify-start'} ml-4 mr-4 mb-2 flex-wrap gap-2`}>
                    {msg.artifactData.documents.map((doc) => (
                      <Button
                        key={doc.id}
                        variant="outline"
                        size="sm"
                        className="h-auto p-3 justify-start bg-card hover:bg-accent/50 border-border text-left"
                        onClick={() => {
                          handleCloseVideo() // Close video if open
                          handleOpenDocument(doc.id)
                        }}
                      >
                        <div className="flex items-center gap-3">
                          <FileText className="h-4 w-4 text-blue-500" />
                          <div className="min-w-0">
                            <span className="text-sm font-medium truncate block max-w-[200px]" title={doc.name}>
                              {doc.name}
                            </span>
                            <div className="text-xs text-muted-foreground whitespace-nowrap">
                              {formatFileSize(doc.size)}
                            </div>
                          </div>
                        </div>
                      </Button>
                    ))}
                  </div>
                )}

                {/* PDF Document artifact indicator - if checking backend logic, PDFs might not be in artifactData 
                    but just in the chat context. 
                    However, if we want to click to view, we should look for them?
                    Current backend only injects them into system context.
                    We need to list them from `attachedDocuments`? 
                    Wait, attachedDocuments are what we are SENDING.
                    Usually we want to see documents already in the chat. 
                    `documentService.getDocumentsForChat`?
                    
                    For now, let's allow clicking from the `AttachedDocument` previews 
                    Use `DocumentPreviewList`? No, that's for input.
                    
                    We don't have a "Chat Files" list yet.
                    But if we want a "Not working like screenshot" behavior, 
                    maybe we just rely on `DocumentPreviewList` in the input area?
                    Or maybe we should add a "Documents" button in the header?
                    
                    The screenshot showed "rag-anything...pdf" in a modal.
                    Maybe it was clicked from a file list?
                    
                    Let's add a `Files` button to the header?
                    Or better, add a way to view attached documents from previous messages?
                    
                    But messages don't store "attached documents" metadata in `artifactData` for PDFs in the current backend logic (only YouTube/Images).
                    The backend `api/chat.py` only sets `artifact_type="image"` or `artifact_type="youtube"`.
                    It does not set `artifact_type="pdf"`.
                    PDFs are uploaded separately via `upload_document`.
                    
                    So we can't click a message bubble for PDFs yet.
                    We should query documents for the chat and list them?
                    
                    Let's update the `ChatDetails` to fetch documents.
                 */}
              </div>
            ))}
            <div ref={scrollAnchorRef} className="h-1" aria-hidden="true" />
          </div>
        </ScrollArea>
      </div>

      {/* Message Input - Unified container */}
      <div className="flex-shrink-0 p-4 border-t border-border bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
        <div ref={messageInputContainerRef} className="border border-border rounded-xl bg-card shadow-sm">
          {/* Image previews */}
          {attachedImages.length > 0 && (
            <ImagePreviewList
              images={attachedImages}
              onRemove={handleRemoveImage}
              onImageClick={(img) => setPreviewImage({ src: img.preview, alt: img.name })}
              disabled={isLoading}
            />
          )}
          {/* Document previews */}
          {attachedDocuments.length > 0 && (
            <DocumentPreviewList
              documents={attachedDocuments}
              onRemove={handleRemoveDocument}
              onDocumentClick={handleOpenDocument}
              disabled={isLoading}
            />
          )}
          {/* Textarea area */}
          <div className="px-3 pt-3 pb-2">
            <Textarea
              ref={textareaRef}
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              placeholder={attachedImages.length > 0 ? "Add a message about the image(s)..." : "Send a message or paste a YouTube URL..."}
              className="flex-1 resize-none overflow-hidden border-0 bg-transparent p-0 focus-visible:ring-0 focus-visible:ring-offset-0 shadow-none min-h-[24px]"
              rows={1}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault()
                  handleSendMessage()
                }
              }}
            />
          </div>
          {/* Bottom bar with actions and send button */}
          <div className="flex items-center justify-between px-3 py-2 border-t border-border/50">
            <div className="flex items-center gap-2">
              <ModelSelector
                selectedProvider={chatProvider}
                selectedModel={chatModel}
                onChange={handleModelChange}
                disabled={isLoading}
                compact
              />
              <ImageAttachment
                images={attachedImages}
                onAdd={handleAddImage}
                disabled={isLoading}
                maxImages={5}
              />
              <DocumentAttachment
                documents={attachedDocuments}
                onAdd={handleAddDocument}
                onUpdate={handleUpdateDocument}
                chatId={conversationIdRef.current || chatId || ''}
                disabled={isLoading}
                maxDocuments={5}
                onEnsureChatId={ensureChatIdForDocument}
              />
              <Button
                variant={thinkingEnabled ? "secondary" : "ghost"}
                size="sm"
                onClick={() => setThinkingEnabled(!thinkingEnabled)}
                disabled={isLoading}
                className="flex items-center gap-1 h-8"
                title={thinkingEnabled ? "Thinking enabled - click to disable" : "Thinking disabled - click to enable"}
              >
                <Brain className={`h-4 w-4 ${thinkingEnabled ? 'text-primary' : 'text-muted-foreground'}`} />
              </Button>
            </div>
            <div className="flex items-center gap-2">
              {(isLoading || isExecutingTools) && (
                <Button
                  variant="destructive"
                  size="sm"
                  onClick={async () => {
                    // Send cancel request to backend
                    if (currentStreamId) {
                      try {
                        await fetch(`${API_BASE_URL}/api/v1/chat/cancel`, {
                          method: 'POST',
                          headers: { 'Content-Type': 'application/json' },
                          body: JSON.stringify({ stream_id: currentStreamId }),
                        })
                      } catch (e) {
                        console.error('Failed to cancel stream:', e)
                      }
                    }
                    // Also abort the fetch request
                    abortController?.abort()
                    setIsExecutingTools(false)
                    setAbortController(null)
                    setCurrentStreamId(null)
                  }}
                  className="flex items-center gap-1 h-8"
                >
                  <Square className="h-3 w-3" />
                  Stop
                </Button>
              )}
              <Button
                onClick={handleSendMessage}
                size="icon"
                disabled={isLoading || (!message.trim() && attachedImages.length === 0)}
                className="rounded-full h-8 w-8"
              >
                {isLoading ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <Send className="h-4 w-4" />
                )}
              </Button>
            </div>
          </div>
        </div>
      </div>
    </div>
  )

  const VideoPanel = (
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
          videoId={currentVideoId || ""}
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
  )

  if (showStackedView) {
    return (
      <div className="h-full flex flex-col">
        {ChatPanel}
        <Sheet open={isVideoSheetOpen} onOpenChange={setIsVideoSheetOpen}>
          <SheetContent side="bottom" className="h-[85vh] p-0 flex flex-col">
            <SheetHeader className="sr-only">
              <SheetTitle>YouTube Video</SheetTitle>
              <SheetDescription>
                Watch video and view transcript
              </SheetDescription>
            </SheetHeader>
            {VideoPanel}
          </SheetContent>
        </Sheet>

        <Sheet open={isDocumentSheetOpen} onOpenChange={setIsDocumentSheetOpen}>
          <SheetContent side="bottom" className="h-[85vh] p-0 flex flex-col">
            <SheetHeader className="sr-only">
              <SheetTitle>Document Viewer</SheetTitle>
              <SheetDescription>View document content</SheetDescription>
            </SheetHeader>
            {currentDocumentId && (
              <div className="h-full flex flex-col relative">
                <Button
                  variant="ghost"
                  size="icon"
                  className="absolute top-2 right-2 z-10 h-8 w-8 bg-background/50 hover:bg-background"
                  onClick={handleCloseDocument}
                >
                  <X className="h-4 w-4" />
                </Button>
                <DocumentViewer
                  documentId={currentDocumentId}
                  onClose={handleCloseDocument}
                />
              </div>
            )}
          </SheetContent>
        </Sheet>
      </div >
    )
  }

  return (
    <div className="h-full flex flex-col">
      <div className="flex-1 overflow-hidden">
        <ResizablePanelGroup direction="horizontal" className="h-full">
          {/* Chat Panel */}
          <ResizablePanel defaultSize={hasSidePanel ? 50 : 100} minSize={30}>
            {ChatPanel}
          </ResizablePanel>

          {/* Side Panel (Video or Document) */}
          {hasSidePanel && (
            <>
              <ResizableHandle withHandle />
              <ResizablePanel defaultSize={50} minSize={30}>
                {hasVideoArtifact ? VideoPanel : (
                  currentDocumentId && (
                    <div className="h-full relative border-l border-border">
                      <Button
                        variant="ghost"
                        size="icon"
                        className="absolute top-2 right-2 z-10 h-8 w-8 bg-background/50 hover:bg-background"
                        onClick={handleCloseDocument}
                      >
                        <X className="h-4 w-4" />
                      </Button>
                      <DocumentViewer
                        documentId={currentDocumentId}
                        onClose={handleCloseDocument}
                      />
                    </div>
                  )
                )}
              </ResizablePanel>
            </>
          )}
        </ResizablePanelGroup>
      </div>

      {/* Image Lightbox */}
      <Dialog open={!!previewImage} onOpenChange={(open) => !open && setPreviewImage(null)}>
        <DialogContent className="max-w-[95vw] max-h-[95vh] p-0 overflow-hidden bg-transparent border-none shadow-none flex items-center justify-center">
          {previewImage && (
            <div className="relative group">
              <img
                src={previewImage.src}
                alt={previewImage.alt || 'Preview'}
                className="max-w-full max-h-[90vh] object-contain rounded-lg shadow-2xl"
              />
              <button
                onClick={() => setPreviewImage(null)}
                className="absolute -top-4 -right-4 h-10 w-10 rounded-full bg-background/80 hover:bg-background border border-border flex items-center justify-center shadow-lg transition-all opacity-0 group-hover:opacity-100"
              >
                <X className="h-5 w-5" />
              </button>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  )
}
