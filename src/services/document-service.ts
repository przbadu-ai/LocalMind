/**
 * Document service for interacting with the backend API.
 *
 * This service provides methods for:
 * - Uploading PDF documents
 * - Getting document metadata and status
 * - Listing documents for a chat
 * - Deleting documents
 */

import { API_BASE_URL } from "@/config/app-config";

export interface Document {
  id: string;
  chat_id: string;
  filename: string;
  original_filename: string;
  mime_type: string;
  file_size: number | null;
  page_count: number | null;
  status: 'pending' | 'processing' | 'completed' | 'error';
  error_message: string | null;
  created_at: string;
  updated_at: string;
}

export interface DocumentChunk {
  id: string;
  chunk_index: number;
  content: string;
  page_number: number | null;
}

export interface DocumentUploadResponse {
  success: boolean;
  document: Document | null;
  error: string | null;
}

export interface DocumentListResponse {
  documents: Document[];
  total: number;
}

export interface DocumentChunksResponse {
  document_id: string;
  chunks: DocumentChunk[];
  total: number;
}

class DocumentService {
  private baseUrl: string;

  constructor() {
    this.baseUrl = `${API_BASE_URL}/api/v1`;
  }

  /**
   * Upload a PDF document for a chat.
   * Note: The backend processes PDFs synchronously, which can take 20-60 seconds.
   */
  async uploadDocument(chatId: string, file: File): Promise<DocumentUploadResponse> {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('chat_id', chatId);

    console.log('[DocumentService] Starting upload for chat:', chatId, 'file:', file.name);

    try {
      const response = await fetch(`${this.baseUrl}/documents/upload`, {
        method: 'POST',
        body: formData,
      });

      console.log('[DocumentService] Response status:', response.status, response.statusText);

      if (!response.ok) {
        const errorText = await response.text();
        console.error('[DocumentService] Upload failed:', errorText);
        return {
          success: false,
          document: null,
          error: `Upload failed: ${response.statusText}`,
        };
      }

      const result = await response.json();
      console.log('[DocumentService] Upload response:', result);
      return result;
    } catch (error) {
      console.error('[DocumentService] Upload exception:', error);
      return {
        success: false,
        document: null,
        error: error instanceof Error ? error.message : 'Upload failed',
      };
    }
  }

  /**
   * Get a document by ID.
   */
  async getDocument(documentId: string): Promise<Document> {
    const response = await fetch(`${this.baseUrl}/documents/${documentId}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      if (response.status === 404) {
        throw new Error('Document not found');
      }
      throw new Error(`Failed to get document: ${response.statusText}`);
    }

    return response.json();
  }

  /**
   * Delete a document.
   */
  async deleteDocument(documentId: string): Promise<void> {
    const response = await fetch(`${this.baseUrl}/documents/${documentId}`, {
      method: 'DELETE',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      throw new Error(`Failed to delete document: ${response.statusText}`);
    }
  }

  /**
   * Get all documents for a chat.
   */
  async getChatDocuments(chatId: string): Promise<DocumentListResponse> {
    const response = await fetch(`${this.baseUrl}/chats/${chatId}/documents`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      throw new Error(`Failed to get documents: ${response.statusText}`);
    }

    return response.json();
  }

  /**
   * Get chunks for a document.
   */
  async getDocumentChunks(documentId: string, limit?: number): Promise<DocumentChunksResponse> {
    const params = new URLSearchParams();
    if (limit) {
      params.append('limit', limit.toString());
    }

    const response = await fetch(`${this.baseUrl}/documents/${documentId}/chunks?${params}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      throw new Error(`Failed to get document chunks: ${response.statusText}`);
    }

    return response.json();
  }

  /**
   * Poll document status until it's completed or errored.
   */
  async pollDocumentStatus(
    documentId: string,
    onStatusChange?: (doc: Document) => void,
    maxAttempts: number = 60,
    intervalMs: number = 1000
  ): Promise<Document> {
    let attempts = 0;

    while (attempts < maxAttempts) {
      const doc = await this.getDocument(documentId);

      if (onStatusChange) {
        onStatusChange(doc);
      }

      if (doc.status === 'completed' || doc.status === 'error') {
        return doc;
      }

      await new Promise(resolve => setTimeout(resolve, intervalMs));
      attempts++;
    }

    throw new Error('Document processing timed out');
  }
}

// Export singleton instance
export const documentService = new DocumentService();

export default documentService;
