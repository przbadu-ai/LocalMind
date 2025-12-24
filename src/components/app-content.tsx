import { useState, useRef, useEffect, useCallback } from "react"
import { Send, Sparkles } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"
import { useNavigate } from "react-router-dom"
import { chatService } from "@/services/chat-service"
import { ModelSelector } from "@/components/ModelSelector"
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
} from "@/components/chat/DocumentAttachment"
import { documentService } from "@/services/document-service"

export function MainContent() {
  const [message, setMessage] = useState("")
  const [isCreatingChat, setIsCreatingChat] = useState(false)
  const [selectedProvider, setSelectedProvider] = useState<string | null>(null)
  const [selectedModel, setSelectedModel] = useState<string | null>(null)
  const [attachedImages, setAttachedImages] = useState<AttachedImage[]>([])
  const [attachedDocuments, setAttachedDocuments] = useState<AttachedDocument[]>([])
  const [draftChatId, setDraftChatId] = useState<string | null>(null)
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const messageInputContainerRef = useRef<HTMLDivElement>(null)
  const draftChatCreatingRef = useRef(false)
  const navigate = useNavigate()

  const handleModelChange = (provider: string, model: string) => {
    setSelectedProvider(provider)
    setSelectedModel(model)
  }

  // Image attachment handlers
  const handleAddImage = useCallback((image: AttachedImage) => {
    setAttachedImages(prev => [...prev, image])
  }, [])

  const handleRemoveImage = useCallback((id: string) => {
    setAttachedImages(prev => prev.filter(img => img.id !== id))
  }, [])

  // Handle paste events for images
  const handleImagePaste = useImagePaste(handleAddImage, {
    enabled: !isCreatingChat,
    maxImages: 5,
    currentCount: attachedImages.length,
  })

  // Document attachment handlers
  const handleAddDocument = useCallback((doc: AttachedDocument) => {
    setAttachedDocuments(prev => [...prev, doc])
  }, [])

  const handleUpdateDocument = useCallback((id: string, updates: Partial<AttachedDocument>) => {
    setAttachedDocuments(prev => prev.map(doc =>
      doc.id === id ? { ...doc, ...updates } : doc
    ))
  }, [])

  const handleRemoveDocument = useCallback(async (id: string) => {
    const doc = attachedDocuments.find(d => d.id === id)
    if (doc?.document?.id) {
      try {
        await documentService.deleteDocument(doc.document.id)
      } catch (error) {
        console.error('Failed to delete document from server:', error)
      }
    }
    setAttachedDocuments(prev => prev.filter(d => d.id !== id))
  }, [attachedDocuments])

  // Ensure a chat exists for document upload
  const ensureChatId = useCallback(async (): Promise<string> => {
    if (draftChatId) return draftChatId
    if (draftChatCreatingRef.current) {
      // Wait for existing creation to finish
      return new Promise((resolve) => {
        const checkInterval = setInterval(() => {
          if (draftChatId) {
            clearInterval(checkInterval)
            resolve(draftChatId)
          }
        }, 100)
      })
    }

    draftChatCreatingRef.current = true
    try {
      const newChat = await chatService.createChat({
        title: 'New Chat'
      })
      setDraftChatId(newChat.id)
      draftChatCreatingRef.current = false
      return newChat.id
    } catch (error) {
      draftChatCreatingRef.current = false
      console.error('Failed to create draft chat:', error)
      throw error
    }
  }, [draftChatId])

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
    // Allow sending if there's text OR if there are attached images/docs
    const hasAttachments = attachedImages.length > 0 || attachedDocuments.length > 0
    if ((!message.trim() && !hasAttachments) || isCreatingChat) return

    setIsCreatingChat(true)
    try {
      // Use a default message if only images/docs are attached
      const messageContent = message.trim() ||
        (attachedImages.length > 0 ? "What's in this image?" :
          attachedDocuments.length > 0 ? "What is in this document?" : "")

      // Use existing draft chat if we have one, otherwise create a new one
      let chatIdToUse = draftChatId
      let newChat = null

      if (chatIdToUse) {
        // Update the draft chat title with the first message
        await chatService.updateChat(chatIdToUse, { title: messageContent.substring(0, 50) })
      } else {
        // Create a new chat
        newChat = await chatService.createChat({
          title: messageContent.substring(0, 50),
          model: selectedModel || undefined,
          provider: selectedProvider || undefined,
        })
        chatIdToUse = newChat.id
      }

      // Capture current images and documents before clearing
      const imagesToSend = [...attachedImages]
      const documentsToSend = [...attachedDocuments]

      // Reset textarea height and clear state
      setMessage("")
      setAttachedImages([])
      setAttachedDocuments([])
      if (textareaRef.current) {
        textareaRef.current.style.height = 'auto'
      }

      // Navigate to the chat detail page
      navigate(`/chats/${chatIdToUse}`, {
        state: {
          initialMessage: messageContent,
          initialImages: imagesToSend,
          initialDocuments: documentsToSend
        }
      })
    } catch (error) {
      console.error('Failed to create chat:', error)
      setIsCreatingChat(false)
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
            <div className="border border-border rounded-xl bg-card shadow-sm" ref={messageInputContainerRef}>
              {/* Image previews */}
              <ImagePreviewList
                images={attachedImages}
                onRemove={handleRemoveImage}
                disabled={isCreatingChat}
              />
              {/* Document previews */}
              <DocumentPreviewList
                documents={attachedDocuments}
                onRemove={handleRemoveDocument}
                disabled={isCreatingChat}
              />
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
                  {/* Image attachment button */}
                  <ImageAttachment
                    images={attachedImages}
                    onAdd={handleAddImage}
                    disabled={isCreatingChat}
                    maxImages={5}
                  />
                  {/* Document attachment button */}
                  <DocumentAttachment
                    documents={attachedDocuments}
                    onAdd={handleAddDocument}
                    onUpdate={handleUpdateDocument}
                    chatId="" // Component will use onEnsureChatId to get the ID
                    onEnsureChatId={ensureChatId}
                    disabled={isCreatingChat}
                    maxDocuments={5}
                  />
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
                  disabled={isCreatingChat || (!message.trim() && attachedImages.length === 0 && attachedDocuments.length === 0)}
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
