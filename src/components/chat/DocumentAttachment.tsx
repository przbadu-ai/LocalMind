import { useCallback, useRef, ChangeEvent } from 'react'
import { Button } from '@/components/ui/button'
import { FileText, X, Loader2, AlertCircle, CheckCircle2 } from 'lucide-react'
import { cn } from '@/lib/utils'
import { Document, documentService } from '@/services/document-service'

export interface AttachedDocument {
  id: string
  file?: File
  name: string
  size: number
  status: 'pending' | 'uploading' | 'processing' | 'completed' | 'error'
  progress?: number
  error?: string
  document?: Document // Backend document record once uploaded
}

interface DocumentAttachmentProps {
  documents: AttachedDocument[]
  onAdd: (doc: AttachedDocument) => void
  onUpdate: (id: string, updates: Partial<AttachedDocument>) => void
  onRemove: (id: string) => void
  chatId: string
  disabled?: boolean
  maxDocuments?: number
  /** Called to ensure a chat exists before uploading. Returns the chat ID. */
  onEnsureChatId?: () => Promise<string>
}

/**
 * Generate a unique ID for an attached document
 */
function generateDocumentId(): string {
  return `doc-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
}

/**
 * Validate that a file is an acceptable document type
 */
function isValidDocumentType(file: File): boolean {
  const validTypes = ['application/pdf']
  return validTypes.includes(file.type)
}

/**
 * Maximum file size in bytes (50MB)
 */
const MAX_FILE_SIZE = 50 * 1024 * 1024

/**
 * Format file size for display
 */
function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

export function DocumentAttachment({
  documents,
  onAdd,
  onUpdate,
  onRemove,
  chatId,
  disabled = false,
  maxDocuments = 5,
  onEnsureChatId,
}: DocumentAttachmentProps) {
  const fileInputRef = useRef<HTMLInputElement>(null)

  const uploadDocument = useCallback(
    async (attachedDoc: AttachedDocument, effectiveChatId: string) => {
      if (!attachedDoc.file) return

      // Update status to processing (backend processes synchronously, so this takes a while)
      onUpdate(attachedDoc.id, { status: 'processing' })

      try {
        console.log('[DocumentAttachment] Starting upload for:', attachedDoc.name)
        const result = await documentService.uploadDocument(effectiveChatId, attachedDoc.file)
        console.log('[DocumentAttachment] Upload result:', result)

        if (result.success && result.document) {
          console.log('[DocumentAttachment] Document status:', result.document.status)
          // Poll for completion if still processing
          if (result.document.status === 'processing' || result.document.status === 'pending') {
            onUpdate(attachedDoc.id, {
              status: 'processing',
              document: result.document,
            })

            // Poll for status updates
            try {
              const finalDoc = await documentService.pollDocumentStatus(
                result.document.id,
                (doc) => {
                  console.log('[DocumentAttachment] Poll status update:', doc.status)
                  onUpdate(attachedDoc.id, {
                    status: doc.status as AttachedDocument['status'],
                    document: doc,
                    error: doc.error_message || undefined,
                  })
                }
              )

              console.log('[DocumentAttachment] Final document status:', finalDoc.status)
              onUpdate(attachedDoc.id, {
                status: finalDoc.status as AttachedDocument['status'],
                document: finalDoc,
                error: finalDoc.error_message || undefined,
              })
            } catch (pollError) {
              console.error('[DocumentAttachment] Poll error:', pollError)
              onUpdate(attachedDoc.id, {
                status: 'error',
                error: 'Processing timed out',
              })
            }
          } else {
            // Document already completed (synchronous processing)
            console.log('[DocumentAttachment] Document completed synchronously:', result.document.status)
            onUpdate(attachedDoc.id, {
              status: result.document.status as AttachedDocument['status'],
              document: result.document,
              error: result.document.error_message || undefined,
            })
          }
        } else {
          console.error('[DocumentAttachment] Upload failed:', result.error)
          onUpdate(attachedDoc.id, {
            status: 'error',
            error: result.error || 'Upload failed',
          })
        }
      } catch (error) {
        console.error('[DocumentAttachment] Exception during upload:', error)
        onUpdate(attachedDoc.id, {
          status: 'error',
          error: error instanceof Error ? error.message : 'Upload failed',
        })
      }
    },
    [onUpdate]
  )

  const handleFileSelect = useCallback(
    async (e: ChangeEvent<HTMLInputElement>) => {
      const files = e.target.files
      if (!files || files.length === 0) return

      // Ensure we have a chat ID before uploading
      let effectiveChatId = chatId
      if (!effectiveChatId && onEnsureChatId) {
        try {
          effectiveChatId = await onEnsureChatId()
        } catch (error) {
          console.error('Failed to create chat for document upload:', error)
          return
        }
      }

      if (!effectiveChatId) {
        console.error('No chat ID available for document upload')
        return
      }

      for (const file of Array.from(files)) {
        // Check if we've reached the max
        if (documents.length >= maxDocuments) {
          console.warn(`Maximum ${maxDocuments} documents allowed`)
          break
        }

        // Validate file type
        if (!isValidDocumentType(file)) {
          console.warn(`Invalid file type: ${file.type}. Only PDF files are supported.`)
          continue
        }

        // Validate file size
        if (file.size > MAX_FILE_SIZE) {
          console.warn(`File too large: ${file.name} (${formatFileSize(file.size)})`)
          continue
        }

        const attachedDoc: AttachedDocument = {
          id: generateDocumentId(),
          file,
          name: file.name,
          size: file.size,
          status: 'pending',
        }

        onAdd(attachedDoc)

        // Start upload with the effective chat ID
        uploadDocument(attachedDoc, effectiveChatId)
      }

      // Reset the input
      if (fileInputRef.current) {
        fileInputRef.current.value = ''
      }
    },
    [chatId, documents.length, maxDocuments, onAdd, onEnsureChatId, uploadDocument]
  )

  const handleButtonClick = useCallback(() => {
    fileInputRef.current?.click()
  }, [])

  const canAddMore = documents.length < maxDocuments

  return (
    <div className="flex items-center gap-2">
      {/* Hidden file input */}
      <input
        ref={fileInputRef}
        type="file"
        accept="application/pdf"
        multiple
        onChange={handleFileSelect}
        className="hidden"
        disabled={disabled}
      />

      {/* Add document button */}
      <Button
        type="button"
        variant="ghost"
        size="icon"
        onClick={handleButtonClick}
        disabled={disabled || !canAddMore}
        className="h-8 w-8 text-muted-foreground hover:text-foreground"
        title={canAddMore ? 'Attach PDF document' : `Maximum ${maxDocuments} documents`}
      >
        <FileText className="h-4 w-4" />
      </Button>
    </div>
  )
}

interface DocumentPreviewListProps {
  documents: AttachedDocument[]
  onRemove: (id: string) => void
  disabled?: boolean
}

/**
 * Displays a list of attached document previews with status and remove buttons
 */
export function DocumentPreviewList({
  documents,
  onRemove,
  disabled = false,
}: DocumentPreviewListProps) {
  if (documents.length === 0) return null

  return (
    <div className="flex flex-col gap-2 p-2">
      {documents.map((doc) => (
        <div
          key={doc.id}
          className={cn(
            'relative group flex items-center gap-3 p-2 rounded-lg border',
            'bg-muted/30 hover:bg-muted/50 transition-colors',
            doc.status === 'error' && 'border-destructive/50 bg-destructive/5'
          )}
        >
          {/* Status icon */}
          <div className="flex-shrink-0">
            {doc.status === 'uploading' || doc.status === 'processing' ? (
              <Loader2 className="h-5 w-5 animate-spin text-primary" />
            ) : doc.status === 'error' ? (
              <AlertCircle className="h-5 w-5 text-destructive" />
            ) : doc.status === 'completed' ? (
              <CheckCircle2 className="h-5 w-5 text-green-500" />
            ) : (
              <FileText className="h-5 w-5 text-muted-foreground" />
            )}
          </div>

          {/* Document info */}
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium truncate" title={doc.name}>
              {doc.name}
            </p>
            <p className="text-xs text-muted-foreground">
              {doc.status === 'uploading' && 'Uploading...'}
              {doc.status === 'processing' && 'Processing...'}
              {doc.status === 'completed' &&
                `${formatFileSize(doc.size)}${doc.document?.page_count ? ` - ${doc.document.page_count} pages` : ''}`}
              {doc.status === 'error' && (
                <span className="text-destructive">{doc.error || 'Failed'}</span>
              )}
              {doc.status === 'pending' && formatFileSize(doc.size)}
            </p>
          </div>

          {/* Remove button */}
          {!disabled && (
            <button
              type="button"
              onClick={() => onRemove(doc.id)}
              className={cn(
                'p-1 rounded-full',
                'bg-background/80 hover:bg-destructive hover:text-destructive-foreground',
                'opacity-0 group-hover:opacity-100 transition-opacity'
              )}
              title="Remove document"
            >
              <X className="h-4 w-4" />
            </button>
          )}
        </div>
      ))}
    </div>
  )
}

/**
 * Format file size helper exported for external use
 */
export { formatFileSize }
