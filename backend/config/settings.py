"""
Application settings management.

This module bridges static application configuration with user preferences,
providing a unified interface for all configuration needs throughout the app.
"""

from pydantic_settings import BaseSettings
from pydantic import Field
from typing import List, Dict, Any, Optional
from pathlib import Path
import os
from .config_manager import get_config_manager, UserConfig, ConfigManager


class Settings(BaseSettings):
    """
    Application settings combining static config with user preferences.

    This class provides:
    1. Static application settings (version, API paths)
    2. User-configurable settings (models, processing params)
    3. Directory management (data, uploads, logs)
    4. LLM provider configuration

    The settings are loaded from:
    - Hard-coded defaults for static values
    - User's JSON config file for preferences
    - Environment variables for development overrides

    Attributes:
        app_name: Application name (static)
        app_version: Current version (static)
        api_prefix: API route prefix
        debug: Development mode flag (from env)
        cors_origins: Allowed CORS origins
        config_manager: User configuration manager instance
        user_config: Current user preferences
        directories: Application directory paths
        embedding_model: Active embedding model name
        chunk_size: Document chunk size for processing
        chunk_overlap: Overlap between chunks
        max_file_size_mb: Maximum upload file size
        ollama_base_url: Ollama server URL
        additional_allowed_hosts: Extra trusted hosts
        data_dir: Main data directory path
        lancedb_dir: Vector database directory
        uploads_dir: Uploaded documents directory
        logs_dir: Application logs directory

    Example:
        ```python
        from config import settings

        # Access static settings
        print(settings.app_version)

        # Access user settings
        print(settings.chunk_size)

        # Get LLM configuration
        llm_config = settings.get_llm_config()
        ```
    """

    # Static app settings (not user-configurable)
    app_name: str = "Local Mind"
    app_version: str = "0.1.0"
    api_prefix: str = "/api/v1"

    # Development mode (can be set via env var for development only)
    debug: bool = Field(default_factory=lambda: os.getenv("DEBUG", "false").lower() == "true")

    # CORS settings (static for desktop app)
    cors_origins: List[str] = Field(default=[
        "http://localhost:1420",
        "tauri://localhost",
        "http://localhost:3000",  # For development
    ])

    # User configuration manager (initialized in __init__)
    config_manager: Optional[ConfigManager] = Field(default=None, exclude=True)
    user_config: Optional[UserConfig] = Field(default=None, exclude=True)
    directories: Dict[str, Path] = Field(default_factory=dict)

    # User settings (loaded from config file)
    embedding_model: str = Field(default="all-MiniLM-L6-v2")
    chunk_size: int = Field(default=512)
    chunk_overlap: int = Field(default=50)
    max_file_size_mb: int = Field(default=50)
    ollama_base_url: str = Field(default="http://localhost:11434")
    additional_allowed_hosts: List[str] = Field(default_factory=list)

    # Directory paths
    data_dir: Optional[Path] = None
    lancedb_dir: Optional[Path] = None
    uploads_dir: Optional[Path] = None
    logs_dir: Optional[Path] = None

    class Config:
        # No .env file for production desktop app
        env_file = None
        arbitrary_types_allowed = True

    def __init__(self, **kwargs):
        """
        Initialize settings by loading user configuration.

        Performs the following:
        1. Loads user configuration from JSON file
        2. Maps user settings to class attributes
        3. Creates necessary directories
        4. Validates configuration

        Args:
            **kwargs: Additional settings overrides

        Side Effects:
            Creates data directories if they don't exist
        """
        super().__init__(**kwargs)
        # Get user configuration
        self.config_manager = get_config_manager()
        self.user_config = self.config_manager.get_config()
        self.directories = self.config_manager.get_directories()

        # Map user config to settings
        self.embedding_model = self.user_config.embedding_model
        self.chunk_size = self.user_config.chunk_size
        self.chunk_overlap = self.user_config.chunk_overlap
        self.max_file_size_mb = self.user_config.max_file_size_mb
        self.ollama_base_url = self.user_config.ollama_base_url
        self.additional_allowed_hosts = self.user_config.additional_hosts

        # Set up directories
        self.data_dir = self.directories["data"]
        self.lancedb_dir = self.directories["lancedb"]
        self.uploads_dir = self.directories["uploads"]
        self.logs_dir = self.directories["logs"]

        # Create directories if they don't exist
        for dir_path in self.directories.values():
            dir_path.mkdir(exist_ok=True, parents=True)

    def get_llm_config(self) -> dict:
        """
        Get current LLM configuration based on user settings.

        Returns the appropriate configuration based on the selected
        LLM provider (ollama, openai, etc.).

        Returns:
            Dict containing:
            - provider: Active provider name
            - base_url: Server URL (for Ollama)
            - model: Model name
            - api_key: API key (for OpenAI)

        Example:
            ```python
            config = settings.get_llm_config()
            if config["provider"] == "ollama":
                client = OllamaClient(config["base_url"])
            ```
        """
        provider = self.user_config.llm_provider

        if provider == "ollama":
            return {
                "provider": "ollama",
                "base_url": self.user_config.ollama_base_url,
                "model": self.user_config.ollama_model
            }
        elif provider == "openai":
            return {
                "provider": "openai",
                "api_key": self.user_config.openai_api_key,
                "model": self.user_config.openai_model
            }
        else:
            # Default to ollama
            return {
                "provider": "ollama",
                "base_url": self.user_config.ollama_base_url,
                "model": self.user_config.ollama_model
            }

    def update_user_config(self, updates: dict):
        """
        Update user configuration and reload settings.

        Applies configuration updates and reinitializes the settings
        to reflect the changes immediately.

        Args:
            updates: Dictionary of configuration fields to update

        Side Effects:
            - Saves configuration to disk
            - Reinitializes all settings
            - May create new directories

        Example:
            ```python
            settings.update_user_config({
                "chunk_size": 1024,
                "embedding_model": "all-mpnet-base-v2"
            })
            ```

        Note:
            This method triggers a full reload, so use sparingly
            in performance-critical sections.
        """
        self.config_manager.update_config(updates)
        # Reload settings
        self.__init__()


# Singleton instance for application-wide access
settings = Settings()
"""
Global settings instance.

Import this instance throughout the application:
```python
from config import settings
```
"""