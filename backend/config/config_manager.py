"""
Configuration manager for desktop application.

This module handles persistent user configuration storage in platform-specific
locations, providing a consistent interface across Windows, macOS, and Linux.

The configuration is stored as JSON for easy editing and portability.
Settings are automatically created with defaults on first run.
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional
import platform
from pydantic import BaseModel


class UserConfig(BaseModel):
    """
    User-configurable settings model.

    Defines all settings that users can modify through the UI or config file.
    Uses Pydantic for validation and type checking.

    Attributes:
        embedding_model: Name of the sentence transformer model
        llm_provider: LLM service provider (ollama, openai, etc.)
        ollama_base_url: Ollama server endpoint
        ollama_model: Selected Ollama model name
        openai_api_key: OpenAI API key (optional)
        openai_model: Selected OpenAI model
        chunk_size: Document chunk size for processing
        chunk_overlap: Overlap between consecutive chunks
        max_file_size_mb: Maximum uploadable file size
        additional_hosts: List of extra allowed host headers
        custom_data_directory: Override for data storage location
        enable_telemetry: Analytics opt-in flag
        theme: UI theme preference
        language: Interface language code

    Example:
        ```python
        config = UserConfig(
            embedding_model="all-MiniLM-L6-v2",
            chunk_size=1024,
            llm_provider="ollama"
        )
        ```
    """
    # Model settings
    embedding_model: str = "all-MiniLM-L6-v2"
    llm_provider: str = "ollama"  # ollama, openai, llamacpp, etc.
    ollama_base_url: str = "http://192.168.1.173:11434"  # Base URL without /v1
    ollama_model: str = "gpt-oss:latest"
    openai_api_key: Optional[str] = None
    openai_model: str = "gpt-3.5-turbo"

    # Document processing
    chunk_size: int = 512
    chunk_overlap: int = 50
    max_file_size_mb: int = 50

    # Advanced settings
    additional_hosts: list = []
    custom_data_directory: Optional[str] = None
    enable_telemetry: bool = False
    theme: str = "system"  # system, light, dark
    language: str = "en"


class ConfigManager:
    """
    Manages application configuration with OS-specific storage.

    Provides a unified interface for configuration management across platforms,
    handling file I/O, validation, and directory creation.

    The configuration is stored in platform-specific locations:
    - Windows: %APPDATA%/LocalMind/config.json
    - macOS: ~/Library/Application Support/LocalMind/config.json
    - Linux: ~/.config/LocalMind/config.json

    Attributes:
        app_name: Application name for directory creation
        config_dir: Platform-specific configuration directory
        config_file: Path to the JSON configuration file
        config: Current UserConfig instance

    Example:
        ```python
        manager = ConfigManager()
        config = manager.get_config()
        manager.update_config({"chunk_size": 1024})
        ```
    """

    def __init__(self, app_name: str = "LocalMind"):
        """
        Initialize the configuration manager.

        Args:
            app_name: Application name used for directory naming

        Side Effects:
            - Creates config directory if it doesn't exist
            - Creates default config file on first run
        """
        self.app_name = app_name
        self.config_dir = self._get_config_directory()
        self.config_file = self.config_dir / "config.json"
        self.config = self._load_config()

    def _get_config_directory(self) -> Path:
        """
        Get the appropriate config directory for the OS.

        Determines the correct configuration directory based on the
        operating system and platform conventions.

        Returns:
            Path to the configuration directory

        Platform Paths:
            - Windows: Uses %APPDATA% environment variable
            - macOS: Uses ~/Library/Application Support
            - Linux: Uses XDG_CONFIG_HOME or ~/.config

        Side Effects:
            Creates the directory if it doesn't exist
        """
        system = platform.system()

        if system == "Windows":
            # %APPDATA%/LocalMind
            base_dir = Path(os.environ.get('APPDATA', Path.home() / 'AppData' / 'Roaming'))
        elif system == "Darwin":  # macOS
            # ~/Library/Application Support/LocalMind
            base_dir = Path.home() / "Library" / "Application Support"
        else:  # Linux and others
            # ~/.config/LocalMind
            base_dir = Path(os.environ.get('XDG_CONFIG_HOME', Path.home() / '.config'))

        config_dir = base_dir / self.app_name
        config_dir.mkdir(parents=True, exist_ok=True)
        return config_dir

    def _get_data_directory(self) -> Path:
        """
        Get the appropriate data directory for the OS.

        Determines where application data should be stored based on
        platform conventions or user override.

        Returns:
            Path to the data directory

        Priority:
            1. User-specified custom directory
            2. Platform-specific default location

        Platform Defaults:
            - Windows: %LOCALAPPDATA%/LocalMind/data
            - macOS: ~/Library/Application Support/LocalMind/data
            - Linux: ~/.local/share/LocalMind

        Side Effects:
            Creates the directory if it doesn't exist
        """
        # Check if user has specified a custom directory
        if self.config.custom_data_directory:
            return Path(self.config.custom_data_directory)

        system = platform.system()

        if system == "Windows":
            # %LOCALAPPDATA%/LocalMind/data
            base_dir = Path(os.environ.get('LOCALAPPDATA', Path.home() / 'AppData' / 'Local'))
        elif system == "Darwin":  # macOS
            # ~/Library/Application Support/LocalMind/data
            base_dir = Path.home() / "Library" / "Application Support"
        else:  # Linux and others
            # ~/.local/share/LocalMind
            base_dir = Path(os.environ.get('XDG_DATA_HOME', Path.home() / '.local' / 'share'))

        data_dir = base_dir / self.app_name / "data"
        data_dir.mkdir(parents=True, exist_ok=True)
        return data_dir

    def _load_config(self) -> UserConfig:
        """
        Load configuration from file or create default.

        Attempts to load existing configuration, falling back to
        defaults if the file doesn't exist or is corrupted.

        Returns:
            UserConfig instance with loaded or default settings

        Error Handling:
            - Missing file: Creates new with defaults
            - Invalid JSON: Falls back to defaults
            - Validation errors: Falls back to defaults

        Side Effects:
            Creates config file if it doesn't exist
        """
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    config_data = json.load(f)
                return UserConfig(**config_data)
            except Exception as e:
                print(f"Error loading config: {e}")
                return UserConfig()
        else:
            # Create default config
            config = UserConfig()
            self.save_config(config)
            return config

    def save_config(self, config: Optional[UserConfig] = None):
        """
        Save configuration to file.

        Persists the current configuration to JSON file with
        pretty formatting for manual editing.

        Args:
            config: Optional UserConfig to save (uses current if None)

        Side Effects:
            Writes to config.json file

        File Format:
            JSON with 2-space indentation for readability
        """
        if config:
            self.config = config

        with open(self.config_file, 'w') as f:
            json.dump(self.config.model_dump(), f, indent=2)

    def update_config(self, updates: Dict[str, Any]):
        """
        Update specific configuration values.

        Merges the provided updates with existing configuration
        and saves to disk.

        Args:
            updates: Dictionary of configuration keys and new values

        Example:
            ```python
            config_manager.update_config({
                "ollama_base_url": "http://192.168.1.100:11434",
                "chunk_size": 1024
            })
            ```
        """
        config_dict = self.config.model_dump()
        config_dict.update(updates)
        self.config = UserConfig(**config_dict)
        self.save_config()

    def get_config(self) -> UserConfig:
        """
        Get current configuration object.

        Returns:
            UserConfig instance with current settings
        """
        return self.config

    def reset_to_defaults(self):
        """
        Reset configuration to default values.

        Useful for troubleshooting or starting fresh.
        Creates a new default configuration and saves it.
        """
        self.config = UserConfig()
        self.save_config()

    def get_directories(self) -> Dict[str, Path]:
        """
        Get all application directories.

        Returns paths for:
        - config: Configuration files
        - data: Application data
        - lancedb: Vector database
        - uploads: Uploaded documents
        - logs: Application logs

        Returns:
            Dictionary mapping directory names to Path objects
        """
        data_dir = self._get_data_directory()
        return {
            "config": self.config_dir,
            "data": data_dir,
            "lancedb": data_dir / "lancedb",
            "uploads": data_dir / "uploads",
            "logs": self.config_dir / "logs"
        }


# Singleton instance
_config_manager: Optional[ConfigManager] = None


def get_config_manager() -> ConfigManager:
    """
    Get the singleton config manager instance.

    Ensures only one ConfigManager exists throughout the application
    lifecycle, providing consistent configuration access.

    Returns:
        ConfigManager: The global configuration manager instance

    Thread Safety:
        Not thread-safe. Should be called from main thread only.

    Example:
        ```python
        from config.config_manager import get_config_manager

        config_manager = get_config_manager()
        current_config = config_manager.get_config()
        ```
    """
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager