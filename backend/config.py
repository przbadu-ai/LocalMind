"""Configuration management using Pydantic Settings."""

import json
from functools import lru_cache
from pathlib import Path
from typing import Literal, Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


def _load_app_config() -> dict:
    """Load app.config.json if it exists.

    Checks multiple locations for Docker and local development compatibility:
    1. Same directory as config.py (for Docker: /app/app.config.json)
    2. Parent directory (for local dev: project_root/app.config.json)
    """
    # Check in the same directory first (Docker mount location)
    config_path = Path(__file__).parent / "app.config.json"
    if config_path.exists():
        with open(config_path) as f:
            return json.load(f)

    # Fall back to parent directory (local development)
    config_path = Path(__file__).parent.parent / "app.config.json"
    if config_path.exists():
        with open(config_path) as f:
            return json.load(f)

    return {}


class Settings(BaseSettings):
    """Application settings loaded from environment variables and .env file.

    LLM settings should be configured via the Settings page in the app.
    These will be stored in the database and override these defaults.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # LLM Configuration - configure via Settings page
    llm_provider: Literal["ollama", "openai", "llamacpp"] = Field(
        default="ollama",
        description="LLM provider to use",
    )
    llm_base_url: str = Field(
        default="",
        description="Base URL for OpenAI-compatible API (configure in Settings)",
    )
    llm_api_key: str = Field(
        default="",
        description="API key for LLM provider",
    )
    llm_model: str = Field(
        default="",
        description="Default model to use (configure in Settings)",
    )

    # Backend Server
    backend_host: str = Field(
        default="0.0.0.0",
        description="Host to bind the server to (0.0.0.0 for network access)",
    )
    backend_port: int = Field(
        default=52817,
        description="Port to bind the server to",
    )

    # Database
    database_path: str = Field(
        default="./data/local_mind.db",
        description="Path to SQLite database file",
    )

    @property
    def database_full_path(self) -> Path:
        """Get the full path to the database file."""
        return Path(self.database_path).resolve()

    @property
    def cors_origins(self) -> list[str]:
        """Get CORS origins from app.config.json or defaults."""
        try:
            config = _load_app_config()
            return config.get("backend", {}).get("cors_origins", self._default_cors_origins)
        except Exception:
            return self._default_cors_origins

    @property
    def _default_cors_origins(self) -> list[str]:
        return [
            "http://localhost:1420",
            "tauri://localhost",
            "http://0.0.0.0:1420",
            # Allow all origins in development (for mobile/other PC access)
            "*",
        ]


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Global settings instance
settings = get_settings()
