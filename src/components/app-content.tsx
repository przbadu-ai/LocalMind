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

export function MainContent() {
  const [message, setMessage] = useState("")
  const [isCreatingChat, setIsCreatingChat] = useState(false)
  const [selectedProvider, setSelectedProvider] = useState<string | null>(null)
  const [selectedModel, setSelectedModel] = useState<string | null>(null)
  const [attachedImages, setAttachedImages] = useState<AttachedImage[]>([])
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const messageInputContainerRef = useRef<HTMLDivElement>(null)
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
    // Allow sending if there's text OR if there are attached images
    if ((!message.trim() && attachedImages.length === 0) || isCreatingChat) return
    
    setIsCreatingChat(true)
    try {
      // Use a default message if only images are attached
      const messageContent = message.trim() || (attachedImages.length > 0 ? "What's in this image?" : "")
      
      // Create a new chat with the message as the title and selected model
      const newChat = await chatService.createChat({
        title: messageContent.substring(0, 50),
        model: selectedModel || undefined,
        provider: selectedProvider || undefined,
      })

      // Capture current images before clearing
      const imagesToSend = [...attachedImages]

      // Reset textarea height and clear state
      setMessage("")
      setAttachedImages([])
      if (textareaRef.current) {
        textareaRef.current.style.height = 'auto'
      }

      // Navigate to the chat detail page with the message and images in state
      navigate(`/chats/${newChat.id}`, {
        state: { 
          initialMessage: messageContent,
          initialImages: imagesToSend
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
                  disabled={isCreatingChat || (!message.trim() && attachedImages.length === 0)}
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
