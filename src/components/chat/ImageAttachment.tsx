import { useCallback, useRef, ChangeEvent } from 'react'
import { Button } from '@/components/ui/button'
import { ImagePlus, X } from 'lucide-react'
import { cn } from '@/lib/utils'

export interface AttachedImage {
  id: string
  data: string // Base64 data (without data: prefix)
  mimeType: string
  preview: string // Data URL for preview
  name?: string
}

interface ImageAttachmentProps {
  images: AttachedImage[]
  onAdd: (image: AttachedImage) => void
  disabled?: boolean
  maxImages?: number
}

/**
 * Convert a File to base64 format
 */
export function fileToBase64(file: File): Promise<{ data: string; mimeType: string; preview: string }> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => {
      const result = reader.result as string
      // result is in format: data:image/png;base64,XXXX...
      const [header, base64Data] = result.split(',')
      const mimeType = header.match(/data:(.*?);/)?.[1] || 'image/png'
      resolve({
        data: base64Data,
        mimeType,
        preview: result, // Full data URL for preview
      })
    }
    reader.onerror = () => reject(new Error('Failed to read file'))
    reader.readAsDataURL(file)
  })
}

/**
 * Generate a unique ID for an attached image
 */
function generateImageId(): string {
  return `img-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
}

/**
 * Validate that a file is an acceptable image type
 */
function isValidImageType(file: File): boolean {
  const validTypes = ['image/png', 'image/jpeg', 'image/gif', 'image/webp']
  return validTypes.includes(file.type)
}

/**
 * Maximum file size in bytes (10MB)
 */
const MAX_FILE_SIZE = 10 * 1024 * 1024

export function ImageAttachment({
  images,
  onAdd,
  disabled = false,
  maxImages = 5,
}: ImageAttachmentProps) {
  const fileInputRef = useRef<HTMLInputElement>(null)

  const handleFileSelect = useCallback(
    async (e: ChangeEvent<HTMLInputElement>) => {
      const files = e.target.files
      if (!files || files.length === 0) return

      for (const file of Array.from(files)) {
        // Check if we've reached the max
        if (images.length >= maxImages) {
          console.warn(`Maximum ${maxImages} images allowed`)
          break
        }

        // Validate file type
        if (!isValidImageType(file)) {
          console.warn(`Invalid file type: ${file.type}`)
          continue
        }

        // Validate file size
        if (file.size > MAX_FILE_SIZE) {
          console.warn(`File too large: ${file.name} (${(file.size / 1024 / 1024).toFixed(2)}MB)`)
          continue
        }

        try {
          const { data, mimeType, preview } = await fileToBase64(file)
          onAdd({
            id: generateImageId(),
            data,
            mimeType,
            preview,
            name: file.name,
          })
        } catch (error) {
          console.error('Failed to process image:', error)
        }
      }

      // Reset the input
      if (fileInputRef.current) {
        fileInputRef.current.value = ''
      }
    },
    [images.length, maxImages, onAdd]
  )

  const handleButtonClick = useCallback(() => {
    fileInputRef.current?.click()
  }, [])

  const canAddMore = images.length < maxImages

  return (
    <div className="flex items-center gap-2">
      {/* Hidden file input */}
      <input
        ref={fileInputRef}
        type="file"
        accept="image/png,image/jpeg,image/gif,image/webp"
        multiple
        onChange={handleFileSelect}
        className="hidden"
        disabled={disabled}
      />

      {/* Add image button */}
      <Button
        type="button"
        variant="ghost"
        size="icon"
        onClick={handleButtonClick}
        disabled={disabled || !canAddMore}
        className="h-8 w-8 text-muted-foreground hover:text-foreground"
        title={canAddMore ? 'Attach image' : `Maximum ${maxImages} images`}
      >
        <ImagePlus className="h-4 w-4" />
      </Button>
    </div>
  )
}

interface ImagePreviewListProps {
  images: AttachedImage[]
  onRemove: (id: string) => void
  disabled?: boolean
}

/**
 * Displays a list of attached image previews with remove buttons
 */
export function ImagePreviewList({ images, onRemove, disabled = false }: ImagePreviewListProps) {
  if (images.length === 0) return null

  return (
    <div className="flex flex-wrap gap-2 p-2">
      {images.map((image) => (
        <div
          key={image.id}
          className={cn(
            'relative group rounded-lg overflow-hidden border border-border bg-muted/30',
            'w-16 h-16 flex items-center justify-center'
          )}
        >
          <img
            src={image.preview}
            alt={image.name || 'Attached image'}
            className="w-full h-full object-cover"
          />
          {!disabled && (
            <button
              type="button"
              onClick={() => onRemove(image.id)}
              className={cn(
                'absolute top-0.5 right-0.5 p-0.5 rounded-full',
                'bg-background/80 hover:bg-destructive hover:text-destructive-foreground',
                'opacity-0 group-hover:opacity-100 transition-opacity'
              )}
              title="Remove image"
            >
              <X className="h-3 w-3" />
            </button>
          )}
        </div>
      ))}
    </div>
  )
}

/**
 * Hook for handling paste events to capture images from clipboard
 */
export function useImagePaste(
  onAdd: (image: AttachedImage) => void,
  options: { enabled?: boolean; maxImages?: number; currentCount?: number } = {}
) {
  const { enabled = true, maxImages = 5, currentCount = 0 } = options

  const handlePaste = useCallback(
    async (e: ClipboardEvent) => {
      if (!enabled) return

      const items = e.clipboardData?.items
      if (!items) return

      for (const item of Array.from(items)) {
        if (item.type.startsWith('image/')) {
          // Check if we've reached the max
          if (currentCount >= maxImages) {
            console.warn(`Maximum ${maxImages} images allowed`)
            return
          }

          e.preventDefault()
          const file = item.getAsFile()
          if (!file) continue

          // Validate file size
          if (file.size > MAX_FILE_SIZE) {
            console.warn(`Pasted image too large: ${(file.size / 1024 / 1024).toFixed(2)}MB`)
            continue
          }

          try {
            const { data, mimeType, preview } = await fileToBase64(file)
            onAdd({
              id: generateImageId(),
              data,
              mimeType,
              preview,
              name: 'Pasted image',
            })
          } catch (error) {
            console.error('Failed to process pasted image:', error)
          }
        }
      }
    },
    [enabled, maxImages, currentCount, onAdd]
  )

  return handlePaste
}
