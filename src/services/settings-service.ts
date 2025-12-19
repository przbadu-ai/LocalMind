/**
 * Settings service for managing application configuration.
 *
 * This service provides methods for:
 * - Getting and updating LLM configuration
 * - Testing LLM connectivity
 * - Managing other application settings
 */

import { API_BASE_URL } from "@/config/app-config";

export interface LLMConfig {
  provider: string;
  base_url: string;
  api_key?: string;
  model: string;
  temperature?: number;
  max_tokens?: number;
}

export interface LLMHealthStatus {
  available: boolean;
  model?: string;
  error?: string;
}

export interface ModelInfo {
  id: string;
  name: string;
  provider?: string;
}

export interface ProviderWithModels {
  name: string;
  label: string;
  is_default: boolean;
  configured_model: string | null;
  models: string[];
  error?: string;
}

export interface AllProvidersResponse {
  providers: ProviderWithModels[];
  default_provider: string | null;
  default_model: string | null;
}

export interface AppSettings {
  llm: LLMConfig;
  features?: {
    youtube_enabled?: boolean;
    mcp_enabled?: boolean;
  };
}

class SettingsService {
  private baseUrl: string;

  constructor() {
    this.baseUrl = `${API_BASE_URL}/api/v1/settings`;
  }

  /**
   * Get all application settings.
   */
  async getSettings(): Promise<AppSettings> {
    const response = await fetch(this.baseUrl, {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
      },
    });

    if (!response.ok) {
      throw new Error(`Failed to get settings: ${response.statusText}`);
    }

    return response.json();
  }

  /**
   * Update application settings.
   */
  async updateSettings(settings: Partial<AppSettings>): Promise<AppSettings> {
    const response = await fetch(this.baseUrl, {
      method: "PUT",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(settings),
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(error.detail || `Failed to update settings: ${response.statusText}`);
    }

    return response.json();
  }

  /**
   * Get LLM configuration.
   */
  async getLLMConfig(): Promise<LLMConfig> {
    const response = await fetch(`${this.baseUrl}/llm`, {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
      },
    });

    if (!response.ok) {
      throw new Error(`Failed to get LLM config: ${response.statusText}`);
    }

    return response.json();
  }

  /**
   * Update LLM configuration.
   */
  async updateLLMConfig(config: Partial<LLMConfig>): Promise<LLMConfig> {
    const response = await fetch(`${this.baseUrl}/llm`, {
      method: "PUT",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(config),
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(error.detail || `Failed to update LLM config: ${response.statusText}`);
    }

    return response.json();
  }

  /**
   * Get available LLM models.
   */
  async getAvailableModels(): Promise<ModelInfo[]> {
    const response = await fetch(`${this.baseUrl}/llm/models`, {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
      },
    });

    if (!response.ok) {
      // Return empty array if we can't fetch models
      return [];
    }

    const data = await response.json();
    return data.models || [];
  }

  /**
   * Test LLM connectivity.
   */
  async testLLMConnection(): Promise<LLMHealthStatus> {
    const response = await fetch(`${this.baseUrl}/llm/health`, {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
      },
    });

    if (!response.ok) {
      return {
        available: false,
        error: response.statusText,
      };
    }

    return response.json();
  }

  /**
   * Test LLM connection with specific configuration.
   */
  async testLLMConnectionWithConfig(config: LLMConfig): Promise<LLMHealthStatus> {
    const response = await fetch(`${this.baseUrl}/llm/test`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(config),
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      return {
        available: false,
        error: error.detail || response.statusText,
      };
    }

    return response.json();
  }

  /**
   * Get all saved providers with their available models.
   * Used for the model selector dropdown.
   */
  async getAllProvidersWithModels(): Promise<AllProvidersResponse> {
    const response = await fetch(`${this.baseUrl}/llm/providers/all-models`, {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
      },
    });

    if (!response.ok) {
      throw new Error(`Failed to get providers with models: ${response.statusText}`);
    }

    return response.json();
  }
}

// Export singleton instance
export const settingsService = new SettingsService();
export default settingsService;
