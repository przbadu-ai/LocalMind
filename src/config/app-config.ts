/**
 * Centralized configuration loader for the frontend.
 * Reads from app.config.json at build time.
 */

import appConfigJson from '../../app.config.json';

export interface AppConfig {
  app: {
    name: string;
    version: string;
    description: string;
  };
  backend: {
    host: string;
    port: number;
    api_base_url: string;
    cors_origins: string[];
  };
  models: {
    embedding: {
      default: string;
      options: string[];
    };
    llm: {
      provider: string;
      default_model: string;
      ollama: {
        host: string;
        port: number;
        base_url: string;
        models: string[];
      };
      openai: {
        base_url: string;
        models: string[];
      };
      llamacpp: {
        host: string;
        port: number;
        base_url: string;
      };
    };
  };
  storage: {
    data_dir: string;
    lancedb_path: string;
    documents_path: string;
    max_upload_size_mb: number;
  };
  processing: {
    chunk_size: number;
    chunk_overlap: number;
    max_chunks_per_query: number;
  };
  features: {
    enable_position_tracking: boolean;
    enable_citations: boolean;
    enable_highlighting: boolean;
    enable_offline_mode: boolean;
  };
}

class ConfigLoader {
  private config: AppConfig;

  constructor() {
    this.config = appConfigJson as AppConfig;
  }

  get(key: string, defaultValue?: any): any {
    const keys = key.split('.');
    let value: any = this.config;

    for (const k of keys) {
      if (value && typeof value === 'object' && k in value) {
        value = value[k];
      } else {
        return defaultValue;
      }
    }

    return value;
  }

  getAll(): AppConfig {
    return this.config;
  }

  // Convenience getters
  get appName(): string {
    return this.config.app.name;
  }

  get appVersion(): string {
    return this.config.app.version;
  }

  get apiBaseUrl(): string {
    return this.config.backend.api_base_url;
  }

  get backendPort(): number {
    return this.config.backend.port;
  }

  get defaultLLMModel(): string {
    return this.config.models.llm.default_model;
  }

  get ollamaBaseUrl(): string {
    return this.config.models.llm.ollama.base_url;
  }

  get ollamaHost(): string {
    return this.config.models.llm.ollama.host;
  }

  get ollamaPort(): number {
    return this.config.models.llm.ollama.port;
  }

  get embeddingModel(): string {
    return this.config.models.embedding.default;
  }

  get isOfflineMode(): boolean {
    return this.config.features.enable_offline_mode;
  }

  get enableCitations(): boolean {
    return this.config.features.enable_citations;
  }

  get enableHighlighting(): boolean {
    return this.config.features.enable_highlighting;
  }
}

// Create singleton instance
export const appConfig = new ConfigLoader();

// Export convenience constants
export const APP_NAME = appConfig.appName;
export const APP_VERSION = appConfig.appVersion;
export const API_BASE_URL = appConfig.apiBaseUrl;
export const BACKEND_PORT = appConfig.backendPort;
export const DEFAULT_LLM_MODEL = appConfig.defaultLLMModel;
export const OLLAMA_BASE_URL = appConfig.ollamaBaseUrl;
export const OLLAMA_HOST = appConfig.ollamaHost;
export const OLLAMA_PORT = appConfig.ollamaPort;
export const EMBEDDING_MODEL = appConfig.embeddingModel;