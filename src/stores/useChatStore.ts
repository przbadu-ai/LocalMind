import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { Chat, Message } from "@/services/chat-service";
import type { Transcript } from "@/services/youtube-service";

interface VideoContext {
  videoId: string;
  url: string;
  transcript?: Transcript;
  transcriptAvailable: boolean;
  error?: string;
}

interface ChatState {
  // Current chat
  currentChatId: string | null;
  currentChat: Chat | null;
  messages: Message[];

  // Video context for current chat
  videoContext: VideoContext | null;

  // Chat list
  recentChats: Chat[];

  // Loading states
  isLoading: boolean;
  isStreaming: boolean;
  streamingContent: string;

  // Actions
  setCurrentChat: (chat: Chat | null) => void;
  setCurrentChatId: (chatId: string | null) => void;
  setMessages: (messages: Message[]) => void;
  addMessage: (message: Message) => void;
  updateMessage: (messageId: string, updates: Partial<Message>) => void;

  // Video context actions
  setVideoContext: (context: VideoContext | null) => void;
  updateVideoContext: (updates: Partial<VideoContext>) => void;
  clearVideoContext: () => void;

  // Chat list actions
  setRecentChats: (chats: Chat[]) => void;
  addChat: (chat: Chat) => void;
  updateChat: (chatId: string, updates: Partial<Chat>) => void;
  removeChat: (chatId: string) => void;

  // Loading state actions
  setIsLoading: (loading: boolean) => void;
  setIsStreaming: (streaming: boolean) => void;
  setStreamingContent: (content: string) => void;
  appendStreamingContent: (content: string) => void;
  clearStreamingContent: () => void;

  // Reset
  reset: () => void;
}

const initialState = {
  currentChatId: null,
  currentChat: null,
  messages: [],
  videoContext: null,
  recentChats: [],
  isLoading: false,
  isStreaming: false,
  streamingContent: "",
};

export const useChatStore = create<ChatState>()(
  persist(
    (set, _get) => ({
      ...initialState,

      // Current chat actions
      setCurrentChat: (chat) =>
        set({
          currentChat: chat,
          currentChatId: chat?.id || null,
        }),

      setCurrentChatId: (chatId) => set({ currentChatId: chatId }),

      setMessages: (messages) => set({ messages }),

      addMessage: (message) =>
        set((state) => ({
          messages: [...state.messages, message],
        })),

      updateMessage: (messageId, updates) =>
        set((state) => ({
          messages: state.messages.map((msg) =>
            msg.id === messageId ? { ...msg, ...updates } : msg
          ),
        })),

      // Video context actions
      setVideoContext: (context) => set({ videoContext: context }),

      updateVideoContext: (updates) =>
        set((state) => ({
          videoContext: state.videoContext
            ? { ...state.videoContext, ...updates }
            : null,
        })),

      clearVideoContext: () => set({ videoContext: null }),

      // Chat list actions
      setRecentChats: (chats) => set({ recentChats: chats }),

      addChat: (chat) =>
        set((state) => ({
          recentChats: [chat, ...state.recentChats],
        })),

      updateChat: (chatId, updates) =>
        set((state) => ({
          recentChats: state.recentChats.map((chat) =>
            chat.id === chatId ? { ...chat, ...updates } : chat
          ),
          currentChat:
            state.currentChat?.id === chatId
              ? { ...state.currentChat, ...updates }
              : state.currentChat,
        })),

      removeChat: (chatId) =>
        set((state) => ({
          recentChats: state.recentChats.filter((chat) => chat.id !== chatId),
          currentChat:
            state.currentChat?.id === chatId ? null : state.currentChat,
          currentChatId:
            state.currentChatId === chatId ? null : state.currentChatId,
        })),

      // Loading state actions
      setIsLoading: (loading) => set({ isLoading: loading }),

      setIsStreaming: (streaming) => set({ isStreaming: streaming }),

      setStreamingContent: (content) => set({ streamingContent: content }),

      appendStreamingContent: (content) =>
        set((state) => ({
          streamingContent: state.streamingContent + content,
        })),

      clearStreamingContent: () => set({ streamingContent: "" }),

      // Reset
      reset: () => set(initialState),
    }),
    {
      name: "chat-store",
      partialize: (state) => ({
        // Only persist these fields
        currentChatId: state.currentChatId,
        recentChats: state.recentChats,
      }),
    }
  )
);

// Selectors
export const selectCurrentChat = (state: ChatState) => state.currentChat;
export const selectMessages = (state: ChatState) => state.messages;
export const selectVideoContext = (state: ChatState) => state.videoContext;
export const selectHasVideo = (state: ChatState) => state.videoContext !== null;
export const selectIsLoading = (state: ChatState) => state.isLoading;
export const selectIsStreaming = (state: ChatState) => state.isStreaming;
