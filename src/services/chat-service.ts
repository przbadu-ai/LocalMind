/**
 * Chat service for interacting with the backend API.
 *
 * This service provides methods for:
 * - Creating and managing chats
 * - Loading chat history
 * - Streaming chat messages
 */

import { API_BASE_URL } from "@/config/app-config";

export interface Chat {
  id: string;
  title: string;
  description?: string;
  created_at: string;
  updated_at?: string;
  last_message_at?: string;
  message_count: number;
  is_archived: boolean;
  is_pinned: boolean;
  tags: string[];
  model?: string | null;
  provider?: string | null;
}

export interface ToolCallData {
  id: string;
  name: string;
  arguments: Record<string, unknown>;
  status: 'executing' | 'completed' | 'error' | 'requires_action';
  result?: unknown;
  error?: string;
}

export interface ApproveToolCallRequest {
  conversation_id: string;
  tool_call_id: string;
  approved: boolean;
  tool_name: string;
  tool_args: any;
}


export interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  created_at: string;
  citations?: any[];
  tokens_used?: number;
  confidence_score?: number;
  artifact_type?: 'youtube' | 'pdf' | 'image';
  artifact_data?: {
    video_id?: string;
    url?: string;
    transcript_available?: boolean;
    error?: string;
    images?: Array<{ data: string; mimeType: string; preview?: string }>;
    image_count?: number;
  };
  tool_calls?: ToolCallData[];
}

export interface ChatWithMessages extends Chat {
  messages: Message[];
}

export interface CreateChatRequest {
  title?: string;
  description?: string;
  system_prompt?: string;
  model?: string;
  provider?: string;
  temperature?: number;
}

export interface UpdateChatRequest {
  title?: string;
  description?: string;
  is_archived?: boolean;
  is_pinned?: boolean;
  tags?: string[];
  model?: string;
  provider?: string;
}

class ChatService {
  private baseUrl: string;

  constructor() {
    this.baseUrl = `${API_BASE_URL}/api/v1`;
  }

  /**
   * Create a new chat.
   */
  async createChat(data?: CreateChatRequest): Promise<Chat> {
    const response = await fetch(`${this.baseUrl}/chats`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data || {}),
    });

    if (!response.ok) {
      throw new Error(`Failed to create chat: ${response.statusText}`);
    }

    return response.json();
  }

  /**
   * Get recent chats.
   */
  async getRecentChats(limit: number = 20, includeArchived: boolean = false): Promise<Chat[]> {
    const params = new URLSearchParams({
      limit: limit.toString(),
      include_archived: includeArchived.toString(),
    });

    const response = await fetch(`${this.baseUrl}/chats?${params}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      throw new Error(`Failed to get recent chats: ${response.statusText}`);
    }

    return response.json();
  }

  /**
   * Search chats by query.
   */
  async searchChats(query: string, limit: number = 20): Promise<Chat[]> {
    const params = new URLSearchParams({
      q: query,
      limit: limit.toString(),
    });

    const response = await fetch(`${this.baseUrl}/chats/search?${params}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      throw new Error(`Failed to search chats: ${response.statusText}`);
    }

    return response.json();
  }

  /**
   * Get a specific chat with its messages.
   */
  async getChat(chatId: string, includeMessages: boolean = true): Promise<ChatWithMessages> {
    const params = new URLSearchParams({
      include_messages: includeMessages.toString(),
    });

    const response = await fetch(`${this.baseUrl}/chats/${chatId}?${params}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      if (response.status === 404) {
        throw new Error('Chat not found');
      }
      throw new Error(`Failed to get chat: ${response.statusText}`);
    }

    return response.json();
  }

  /**
   * Update a chat's properties.
   */
  async updateChat(chatId: string, data: UpdateChatRequest): Promise<Chat> {
    const response = await fetch(`${this.baseUrl}/chats/${chatId}`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
    });

    if (!response.ok) {
      throw new Error(`Failed to update chat: ${response.statusText}`);
    }

    return response.json();
  }

  /**
   * Delete a chat.
   */
  async deleteChat(chatId: string): Promise<void> {
    const response = await fetch(`${this.baseUrl}/chats/${chatId}`, {
      method: 'DELETE',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      throw new Error(`Failed to delete chat: ${response.statusText}`);
    }
  }

  /**
   * Get messages for a chat.
   */
  async getChatMessages(chatId: string, limit?: number): Promise<Message[]> {
    const params = new URLSearchParams();
    if (limit) {
      params.append('limit', limit.toString());
    }

    const response = await fetch(`${this.baseUrl}/chats/${chatId}/messages?${params}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      throw new Error(`Failed to get messages: ${response.statusText}`);
    }

    return response.json();
  }

  /**
   * Archive a chat.
   */
  async archiveChat(chatId: string): Promise<void> {
    const response = await fetch(`${this.baseUrl}/chats/${chatId}/archive`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      throw new Error(`Failed to archive chat: ${response.statusText}`);
    }
  }

  /**
   * Pin a chat.
   */
  async pinChat(chatId: string): Promise<void> {
    const response = await fetch(`${this.baseUrl}/chats/${chatId}/pin`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      throw new Error(`Failed to pin chat: ${response.statusText}`);
    }
  }

  /**
   * Unpin a chat.
   */
  async unpinChat(chatId: string): Promise<void> {
    const response = await fetch(`${this.baseUrl}/chats/${chatId}/pin`, {
      method: 'DELETE',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      throw new Error(`Failed to unpin chat: ${response.statusText}`);
    }
  }

  /**
   * Update the model for a specific chat.
   */
  async updateChatModel(chatId: string, provider: string, model: string): Promise<Chat> {
    const response = await fetch(`${this.baseUrl}/chats/${chatId}/model`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ provider, model }),
    });

    if (!response.ok) {
      throw new Error(`Failed to update chat model: ${response.statusText}`);
    }

    return response.json();
  }

  /**
   * Approve or deny a tool call.
   */
  async approveToolCall(data: ApproveToolCallRequest): Promise<any> {
    const response = await fetch(`${this.baseUrl}/chat/tool/approve`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
    });

    if (!response.ok) {
      throw new Error(`Failed to process approval: ${response.statusText}`);
    }

    return response.json();
  }

  /**
   * Stream a chat response.
   * This uses Server-Sent Events to stream the response.
   */
  async *streamChat(message: string, conversationId?: string, options?: {
    temperature?: number;
    max_results?: number;
    include_citations?: boolean;
    resume_from_tool_call?: any;
  }): AsyncGenerator<any, void, unknown> {
    const response = await fetch(`${this.baseUrl}/chat/stream`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        message,
        conversation_id: conversationId,
        temperature: options?.temperature || 0.7,
        max_results: options?.max_results || 5,
        include_citations: options?.include_citations ?? true,
        resume_from_tool_call: options?.resume_from_tool_call,
      }),
    });


    if (!response.ok) {
      throw new Error(`Failed to stream chat: ${response.statusText}`);
    }

    const reader = response.body?.getReader();
    if (!reader) {
      throw new Error('No response body');
    }

    const decoder = new TextDecoder();
    let buffer = '';

    try {
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');

        // Keep the last incomplete line in the buffer
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6));
              yield data;
            } catch (e) {
              // Ignore parse errors
              console.error('Failed to parse SSE data:', e);
            }
          }
        }
      }
    } finally {
      reader.releaseLock();
    }
  }
}

// Export singleton instance
export const chatService = new ChatService();

export default chatService;