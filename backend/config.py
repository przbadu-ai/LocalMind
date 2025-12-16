"""Configuration management using Pydantic Settings."""

import json
from functools import lru_cache
from pathlib import Path
from typing import Literal, Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables and .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # LLM Configuration
    llm_provider: Literal["ollama", "openai", "llamacpp"] = Field(
        default="ollama",
        description="LLM provider to use",
    )
    llm_base_url: str = Field(
        default="http://localhost:8080/v1",
        description="Base URL for OpenAI-compatible API",
    )
    llm_api_key: str = Field(
        default="not-required",
        description="API key for LLM provider",
    )
    llm_model: str = Field(
        default="gpt-oss:latest",
        description="Default model to use",
    )

    # Backend Server
    backend_host: str = Field(
        default="127.0.0.1",
        description="Host to bind the server to",
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
            config = self._load_app_config()
            return config.get("backend", {}).get("cors_origins", self._default_cors_origins)
        except Exception:
            return self._default_cors_origins

    @property
    def _default_cors_origins(self) -> list[str]:
        return [
            "http://localhost:1420",
            "tauri://localhost",
            f"http://{self.backend_host}:1420",
        ]

    @staticmethod
    def _load_app_config() -> dict:
        """Load app.config.json if it exists."""
        config_path = Path(__file__).parent.parent / "app.config.json"
        if config_path.exists():
            with open(config_path) as f:
                return json.load(f)
        return {}


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Global settings instance
settings = get_settings()
