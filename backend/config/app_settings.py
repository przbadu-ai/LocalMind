"""
Centralized configuration loader for the backend.
Reads from app.config.json at the root of the project.
"""

import os
import json
from pathlib import Path
from typing import Any, Dict, Optional
from pydantic import BaseModel


class AppConfig:
    """Singleton configuration loader that reads from app.config.json"""

    _instance = None
    _config: Dict[str, Any] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._load_config()
        return cls._instance

    def _load_config(self):
        """Load configuration from app.config.json"""
        # Find the root directory (where app.config.json is located)
        current_dir = Path(__file__).parent
        root_dir = current_dir.parent.parent  # Go up to project root
        config_path = root_dir / "app.config.json"

        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")

        with open(config_path, 'r') as f:
            self._config = json.load(f)

    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value using dot notation (e.g., 'backend.port')"""
        keys = key.split('.')
        value = self._config

        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
                if value is None:
                    return default
            else:
                return default

        return value

    def get_all(self) -> Dict[str, Any]:
        """Get the entire configuration dictionary"""
        return self._config.copy()

    @property
    def app_name(self) -> str:
        return self.get('app.name', 'Local Mind')

    @property
    def app_version(self) -> str:
        return self.get('app.version', '0.1.0')

    @property
    def backend_host(self) -> str:
        return self.get('backend.host', '127.0.0.1')

    @property
    def backend_port(self) -> int:
        return self.get('backend.port', 52817)

    @property
    def api_base_url(self) -> str:
        return self.get('backend.api_base_url', f'http://{self.backend_host}:{self.backend_port}')

    @property
    def cors_origins(self) -> list:
        return self.get('backend.cors_origins', [])

    @property
    def embedding_model(self) -> str:
        return self.get('models.embedding.default', 'all-MiniLM-L6-v2')

    @property
    def llm_provider(self) -> str:
        return self.get('models.llm.provider', 'ollama')

    @property
    def llm_model(self) -> str:
        return self.get('models.llm.default_model', 'llama3:instruct')

    @property
    def ollama_host(self) -> str:
        return self.get('models.llm.ollama.host', '192.168.1.173')

    @property
    def ollama_port(self) -> int:
        return self.get('models.llm.ollama.port', 11434)

    @property
    def ollama_base_url(self) -> str:
        return self.get('models.llm.ollama.base_url', f'http://{self.ollama_host}:{self.ollama_port}')

    @property
    def data_dir(self) -> str:
        return self.get('storage.data_dir', './data')

    @property
    def lancedb_path(self) -> str:
        return self.get('storage.lancedb_path', './data/lancedb')

    @property
    def chunk_size(self) -> int:
        return self.get('processing.chunk_size', 500)

    @property
    def chunk_overlap(self) -> int:
        return self.get('processing.chunk_overlap', 50)

    @property
    def uploads_dir(self) -> Path:
        """Get the uploads directory path."""
        from pathlib import Path
        documents_path = self.get('storage.documents_path', './data/documents')
        uploads_path = Path(documents_path).absolute()
        uploads_path.mkdir(parents=True, exist_ok=True)
        return uploads_path

    @property
    def max_file_size_mb(self) -> int:
        return self.get('storage.max_upload_size_mb', 100)


# Create a singleton instance
config = AppConfig()

# Helper functions for compatibility
def get_llm_config():
    """Get the active LLM configuration based on provider."""
    provider = config.llm_provider
    if provider == "ollama":
        return {
            "provider": "ollama",
            "base_url": config.ollama_base_url,
            "model": config.llm_model,
            "api_key": None
        }
    elif provider == "openai":
        return {
            "provider": "openai",
            "base_url": config.get('models.llm.openai.base_url'),
            "model": config.get('models.llm.openai.models', ['gpt-3.5-turbo'])[0],
            "api_key": None  # Would come from user config
        }
    elif provider == "llamacpp":
        return {
            "provider": "llamacpp",
            "base_url": config.get('models.llm.llamacpp.base_url'),
            "model": "model.gguf",
            "api_key": None
        }
    else:
        # Default to Ollama
        return {
            "provider": "ollama",
            "base_url": config.ollama_base_url,
            "model": config.llm_model,
            "api_key": None
        }

def get_openai_base_url():
    """Get the OpenAI-compatible API base URL for the current provider."""
    llm_config = get_llm_config()
    base_url = llm_config["base_url"]

    # Add /v1 suffix for OpenAI compatibility if not already present
    if not base_url.endswith("/v1"):
        base_url = f"{base_url}/v1"

    return base_url

# Add helper functions to config instance
config.get_llm_config = get_llm_config
config.get_openai_base_url = get_openai_base_url

# Convenience exports
APP_NAME = config.app_name
APP_VERSION = config.app_version
BACKEND_HOST = config.backend_host
BACKEND_PORT = config.backend_port
API_BASE_URL = config.api_base_url
CORS_ORIGINS = config.cors_origins
EMBEDDING_MODEL = config.embedding_model
LLM_PROVIDER = config.llm_provider
LLM_MODEL = config.llm_model
OLLAMA_HOST = config.ollama_host
OLLAMA_PORT = config.ollama_port
OLLAMA_BASE_URL = config.ollama_base_url
DATA_DIR = config.data_dir
LANCEDB_PATH = config.lancedb_path
CHUNK_SIZE = config.chunk_size
CHUNK_OVERLAP = config.chunk_overlap