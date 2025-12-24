import { useState, useEffect } from "react"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Button } from "@/components/ui/button"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Loader2, AlertCircle, FileText, Eye, ExternalLink, Image as ImageIcon, Music } from "lucide-react"
import { MarkdownRenderer } from "@/components/MarkdownRenderer"
import { documentService, type Document, type DocumentChunk } from "@/services/document-service"
import { Badge } from "@/components/ui/badge"
import { formatFileSize } from "@/components/chat/DocumentAttachment"
import { API_BASE_URL } from "@/config/app-config"
import { X } from "lucide-react"

interface DocumentViewerProps {
    documentId: string
    onClose?: () => void
}

export function DocumentViewer({ documentId, onClose }: DocumentViewerProps) {
    const [document, setDocument] = useState<Document | null>(null)
    const [chunks, setChunks] = useState<DocumentChunk[]>([])
    const [isLoading, setIsLoading] = useState(true)
    const [error, setError] = useState<string | null>(null)

    useEffect(() => {
        const loadDocumentData = async () => {
            setIsLoading(true)
            setError(null)
            try {
                // Fetch document metadata
                const doc = await documentService.getDocument(documentId)
                setDocument(doc)

                // Fetch extracted text chunks
                // Limit to 100 chunks for display to avoid forcing too much data
                const chunksResponse = await documentService.getDocumentChunks(documentId, 100)
                setChunks(chunksResponse.chunks)
            } catch (err) {
                console.error("Failed to load document data:", err)
                setError(err instanceof Error ? err.message : "Failed to load document")
            } finally {
                setIsLoading(false)
            }
        }

        if (documentId) {
            loadDocumentData()
        }
    }, [documentId])

    // Combine chunks into a single markdown string
    const fullText = chunks
        .sort((a, b) => a.chunk_index - b.chunk_index)
        .map(c => c.content)
        .join("\n\n")

    if (isLoading) {
        return (
            <div className="flex items-center justify-center h-full">
                <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
            </div>
        )
    }

    if (error) {
        return (
            <div className="flex flex-col items-center justify-center h-full p-6 text-center">
                <AlertCircle className="h-10 w-10 text-destructive mb-4" />
                <h3 className="text-lg font-semibold text-destructive mb-2">Error Loading Document</h3>
                <p className="text-muted-foreground">{error}</p>
            </div>
        )
    }

    if (!document) return null

    return (
        <div className="h-full flex flex-col bg-background">
            {/* Header */}
            <div className="flex-shrink-0 p-3 border-b border-border flex items-center justify-between bg-card/50">
                <div className="flex items-center gap-3 overflow-hidden">
                    <div className="h-10 w-10 rounded-lg bg-primary/10 flex items-center justify-center flex-shrink-0">
                        {document.mime_type.startsWith('image/') ? (
                            <ImageIcon className="h-5 w-5 text-primary" />
                        ) : document.mime_type.startsWith('audio/') ? (
                            <Music className="h-5 w-5 text-primary" />
                        ) : (
                            <FileText className="h-5 w-5 text-primary" />
                        )}
                    </div>
                    <div className="min-w-0">
                        <h3 className="font-semibold text-sm truncate" title={document.original_filename}>
                            {document.original_filename}
                        </h3>
                        <p className="text-xs text-muted-foreground flex items-center gap-2">
                            {formatFileSize(document.file_size || 0)}
                            <span className="w-1 h-1 rounded-full bg-muted-foreground/30" />
                            {chunks.length} extracted chunks
                        </p>
                    </div>
                </div>

                {/* Status Badge */}
                <div className="flex items-center gap-2">
                    <Badge variant={document.status === 'completed' ? 'secondary' : 'outline'}>
                        {document.status}
                    </Badge>
                    {onClose && (
                        <Button variant="ghost" size="icon" className="h-8 w-8 text-muted-foreground hover:text-foreground" onClick={onClose}>
                            <X className="h-4 w-4" />
                        </Button>
                    )}
                </div>
            </div>

            {/* Tabs */}
            <Tabs defaultValue="content" className="flex-1 flex flex-col overflow-hidden">
                <div className="px-3 pt-2 border-b border-border/50 bg-muted/20">
                    <TabsList className="w-full justify-start h-9 bg-transparent p-0 gap-2">
                        <TabsTrigger
                            value="content"
                            className="data-[state=active]:bg-background data-[state=active]:shadow-sm border border-transparent data-[state=active]:border-border/50 text-xs px-4 h-7 rounded-sm"
                        >
                            <FileText className="h-3 w-3 mr-2" />
                            Content
                        </TabsTrigger>
                        <TabsTrigger
                            value="preview"
                            className="data-[state=active]:bg-background data-[state=active]:shadow-sm border border-transparent data-[state=active]:border-border/50 text-xs px-4 h-7 rounded-sm"
                        >
                            <Eye className="h-3 w-3 mr-2" />
                            Preview
                        </TabsTrigger>
                    </TabsList>
                </div>

                <TabsContent value="content" className="flex-1 overflow-hidden mt-0 p-0">
                    <ScrollArea className="h-full">
                        <div className="p-6 max-w-3xl mx-auto">
                            {chunks.length > 0 ? (
                                <MarkdownRenderer content={fullText} />
                            ) : (
                                <div className="text-center py-10 text-muted-foreground">
                                    <p>No text content extracted.</p>
                                </div>
                            )}
                        </div>
                    </ScrollArea>
                </TabsContent>

                <TabsContent value="preview" className="flex-1 overflow-hidden mt-0">
                    {document?.file_url ? (
                        <div className="h-full w-full bg-muted/5 flex flex-col">
                            <div className="flex-1 w-full overflow-auto flex items-center justify-center p-4">
                                {document.mime_type.startsWith('image/') ? (
                                    <img
                                        src={`${API_BASE_URL}${document.file_url}`}
                                        alt={document.original_filename}
                                        className="max-w-full max-h-full object-contain shadow-lg rounded-md"
                                    />
                                ) : document.mime_type.startsWith('audio/') ? (
                                    <div className="flex flex-col items-center gap-6 p-8 bg-card rounded-xl border shadow-sm w-full max-w-md">
                                        <div className="h-20 w-20 rounded-full bg-primary/10 flex items-center justify-center">
                                            <Music className="h-10 w-10 text-primary" />
                                        </div>
                                        <div className="text-center">
                                            <p className="font-medium text-sm mb-1 truncate max-w-[250px]">{document.original_filename}</p>
                                            <p className="text-xs text-muted-foreground">{formatFileSize(document.file_size || 0)}</p>
                                        </div>
                                        <audio
                                            controls
                                            src={`${API_BASE_URL}${document.file_url}`}
                                            className="w-full"
                                        />
                                    </div>
                                ) : (
                                    <iframe
                                        src={`${API_BASE_URL}${document.file_url}`}
                                        className="w-full h-full border-0"
                                        title={`Preview: ${document.original_filename}`}
                                    />
                                )}
                            </div>
                            <div className="p-2 border-t border-border flex justify-end bg-card/50">
                                <a
                                    href={`${API_BASE_URL}${document.file_url}`}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="text-[10px] text-muted-foreground hover:text-primary flex items-center gap-1.5 transition-colors"
                                >
                                    Open in New Tab
                                    <ExternalLink className="h-2.5 w-2.5" />
                                </a>
                            </div>
                        </div>
                    ) : (
                        <div className="flex flex-col items-center justify-center h-full text-center p-6 text-muted-foreground bg-muted/10">
                            <FileText className="h-16 w-16 mb-4 opacity-20" />
                            <p className="font-medium">PDF Preview Not Available</p>
                            <p className="text-sm max-w-sm mt-2">
                                Original file storage is not enabled for this document.
                                <br />
                                <span className="opacity-70 text-xs">
                                    Only newer documents correctly persist the original file.
                                </span>
                            </p>
                        </div>
                    )}
                </TabsContent>
            </Tabs>
        </div>
    )
}
