"""
Application settings management - Backward compatibility wrapper.

This module provides backward compatibility for code that still uses the old settings import.
All configuration now comes from app.config.json via app_settings.py.
"""

from .app_settings import (
    config,
    APP_NAME,
    APP_VERSION,
    BACKEND_HOST,
    BACKEND_PORT,
    API_BASE_URL,
    CORS_ORIGINS,
    EMBEDDING_MODEL,
    LLM_MODEL,
    OLLAMA_BASE_URL,
    DATA_DIR,
    LANCEDB_PATH,
    CHUNK_SIZE,
    CHUNK_OVERLAP
)


class Settings:
    """
    Backward compatibility wrapper for the old settings interface.
    All properties now delegate to the centralized app_config.
    """

    def __init__(self):
        self._config = config

    @property
    def app_name(self):
        return APP_NAME

    @property
    def app_version(self):
        return APP_VERSION

    @property
    def api_prefix(self):
        return "/api/v1"

    @property
    def debug(self):
        return True

    @property
    def cors_origins(self):
        return CORS_ORIGINS

    @property
    def embedding_model(self):
        return EMBEDDING_MODEL

    @property
    def chunk_size(self):
        return CHUNK_SIZE

    @property
    def chunk_overlap(self):
        return CHUNK_OVERLAP

    @property
    def max_file_size_mb(self):
        return self._config.max_file_size_mb

    @property
    def ollama_base_url(self):
        return OLLAMA_BASE_URL

    @property
    def ollama_model(self):
        return LLM_MODEL

    @property
    def data_dir(self):
        from pathlib import Path
        return Path(DATA_DIR).absolute()

    @property
    def lancedb_dir(self):
        from pathlib import Path
        return Path(LANCEDB_PATH).absolute()

    @property
    def uploads_dir(self):
        return self._config.uploads_dir

    @property
    def logs_dir(self):
        from pathlib import Path
        logs_path = self.data_dir / "logs"
        logs_path.mkdir(parents=True, exist_ok=True)
        return logs_path

    @property
    def additional_allowed_hosts(self):
        return []

    def get_llm_config(self):
        """Get the active LLM configuration."""
        return self._config.get_llm_config()

    def get_openai_base_url(self):
        """Get OpenAI-compatible base URL."""
        return self._config.get_openai_base_url()


# Create singleton instance for backward compatibility
settings = Settings()

__all__ = ["settings"]