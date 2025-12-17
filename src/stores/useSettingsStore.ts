import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { LLMConfig } from "@/services/settings-service";
import type { MCPServer } from "@/services/mcp-service";

interface SettingsState {
  // LLM Configuration
  llmConfig: LLMConfig | null;
  isLLMConnected: boolean;

  // MCP Servers
  mcpServers: MCPServer[];
  runningServers: Set<string>;

  // UI state
  isLoading: boolean;
  lastError: string | null;

  // LLM actions
  setLLMConfig: (config: LLMConfig | null) => void;
  updateLLMConfig: (updates: Partial<LLMConfig>) => void;
  setIsLLMConnected: (connected: boolean) => void;

  // MCP server actions
  setMCPServers: (servers: MCPServer[]) => void;
  addMCPServer: (server: MCPServer) => void;
  updateMCPServer: (serverId: string, updates: Partial<MCPServer>) => void;
  removeMCPServer: (serverId: string) => void;
  setServerRunning: (serverId: string, running: boolean) => void;

  // UI actions
  setIsLoading: (loading: boolean) => void;
  setLastError: (error: string | null) => void;

  // Reset
  reset: () => void;
}

const initialState = {
  llmConfig: null,
  isLLMConnected: false,
  mcpServers: [],
  runningServers: new Set<string>(),
  isLoading: false,
  lastError: null,
};

export const useSettingsStore = create<SettingsState>()(
  persist(
    (set, _get) => ({
      ...initialState,

      // LLM actions
      setLLMConfig: (config) => set({ llmConfig: config }),

      updateLLMConfig: (updates) =>
        set((state) => ({
          llmConfig: state.llmConfig
            ? { ...state.llmConfig, ...updates }
            : null,
        })),

      setIsLLMConnected: (connected) => set({ isLLMConnected: connected }),

      // MCP server actions
      setMCPServers: (servers) => set({ mcpServers: servers }),

      addMCPServer: (server) =>
        set((state) => ({
          mcpServers: [...state.mcpServers, server],
        })),

      updateMCPServer: (serverId, updates) =>
        set((state) => ({
          mcpServers: state.mcpServers.map((server) =>
            server.id === serverId ? { ...server, ...updates } : server
          ),
        })),

      removeMCPServer: (serverId) =>
        set((state) => ({
          mcpServers: state.mcpServers.filter(
            (server) => server.id !== serverId
          ),
          runningServers: new Set(
            Array.from(state.runningServers).filter((id) => id !== serverId)
          ),
        })),

      setServerRunning: (serverId, running) =>
        set((state) => {
          const newRunningServers = new Set(state.runningServers);
          if (running) {
            newRunningServers.add(serverId);
          } else {
            newRunningServers.delete(serverId);
          }
          return { runningServers: newRunningServers };
        }),

      // UI actions
      setIsLoading: (loading) => set({ isLoading: loading }),

      setLastError: (error) => set({ lastError: error }),

      // Reset
      reset: () => set(initialState),
    }),
    {
      name: "settings-store",
      partialize: (state) => ({
        // Only persist LLM config
        llmConfig: state.llmConfig,
      }),
      // Custom serializer to handle Set
      storage: {
        getItem: (name) => {
          const str = localStorage.getItem(name);
          if (!str) return null;
          const parsed = JSON.parse(str);
          return {
            ...parsed,
            state: {
              ...parsed.state,
              runningServers: new Set(),
            },
          };
        },
        setItem: (name, value) => {
          localStorage.setItem(name, JSON.stringify(value));
        },
        removeItem: (name) => localStorage.removeItem(name),
      },
    }
  )
);

// Selectors
export const selectLLMConfig = (state: SettingsState) => state.llmConfig;
export const selectIsLLMConnected = (state: SettingsState) =>
  state.isLLMConnected;
export const selectMCPServers = (state: SettingsState) => state.mcpServers;
export const selectRunningServers = (state: SettingsState) =>
  state.runningServers;
export const selectIsServerRunning = (serverId: string) => (state: SettingsState) =>
  state.runningServers.has(serverId);
