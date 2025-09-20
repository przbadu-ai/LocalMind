"""
Configuration API endpoints for managing application settings.

This module provides REST APIs for reading and updating user configuration,
testing LLM connections, and managing application preferences.
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any
from config.settings import settings
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/config")
async def get_configuration():
    """
    Get current user configuration.

    Retrieves all user-configurable settings including:
    - Model configurations (embedding, LLM)
    - Processing parameters (chunk size, overlap)
    - Application preferences (theme, language)
    - Directory paths

    Sensitive information like API keys are masked in the response.

    Returns:
        Dict containing:
        - config: Current user configuration
        - directories: Application directory paths
        - app_version: Current application version

    Raises:
        HTTPException: 500 if configuration retrieval fails

    Example:
        ```python
        response = requests.get("/api/v1/config")
        # Returns:
        # {
        #   "config": {"embedding_model": "all-MiniLM-L6-v2", ...},
        #   "directories": {"data": "/path/to/data", ...},
        #   "app_version": "0.1.0"
        # }
        ```
    """
    try:
        user_config = settings.user_config.model_dump()
        # Remove sensitive data from response
        if "openai_api_key" in user_config and user_config["openai_api_key"]:
            user_config["openai_api_key"] = "***" + user_config["openai_api_key"][-4:]

        return {
            "config": user_config,
            "directories": {k: str(v) for k, v in settings.directories.items()},
            "app_version": settings.app_version
        }
    except Exception as e:
        logger.error(f"Failed to get configuration: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/config")
async def update_configuration(updates: Dict[str, Any]):
    """
    Update user configuration.

    Allows updating specific configuration fields without affecting others.
    Only whitelisted fields can be updated for security.

    Args:
        updates: Dictionary of configuration fields to update

    Allowed fields:
        - embedding_model: Sentence transformer model name
        - llm_provider: LLM provider (ollama, openai, llamacpp)
        - ollama_base_url: Ollama server URL
        - ollama_model: Ollama model name
        - openai_api_key: OpenAI API key
        - openai_model: OpenAI model name
        - chunk_size: Document chunk size (256-2048)
        - chunk_overlap: Chunk overlap size (0-200)
        - max_file_size_mb: Maximum file size in MB
        - additional_hosts: List of additional allowed hosts
        - custom_data_directory: Custom data storage path
        - enable_telemetry: Telemetry opt-in flag
        - theme: UI theme (system, light, dark)
        - language: Interface language

    Returns:
        Success message with applied updates

    Raises:
        HTTPException: 400 if invalid fields are provided
        HTTPException: 500 if update fails

    Example:
        ```python
        response = requests.put("/api/v1/config", json={
            "chunk_size": 1024,
            "ollama_base_url": "http://192.168.1.100:11434"
        })
        ```
    """
    try:
        # Validate that we're only updating allowed fields
        allowed_fields = {
            "embedding_model", "llm_provider", "ollama_base_url", "ollama_model",
            "openai_api_key", "openai_model", "chunk_size", "chunk_overlap",
            "max_file_size_mb", "additional_hosts", "custom_data_directory",
            "enable_telemetry", "theme", "language"
        }

        invalid_fields = set(updates.keys()) - allowed_fields
        if invalid_fields:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid configuration fields: {invalid_fields}"
            )

        # Update configuration
        settings.update_user_config(updates)

        return {"message": "Configuration updated successfully", "updates": updates}
    except Exception as e:
        logger.error(f"Failed to update configuration: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/config/reset")
async def reset_configuration():
    """
    Reset configuration to default values.

    Restores all configuration settings to their factory defaults.
    Useful for troubleshooting or starting fresh.

    Returns:
        Success message confirming reset

    Raises:
        HTTPException: 500 if reset fails

    Warning:
        This will clear all custom settings including API keys,
        server URLs, and processing parameters.
    """
    try:
        settings.config_manager.reset_to_defaults()
        settings.__init__()  # Reload settings
        return {"message": "Configuration reset to defaults"}
    except Exception as e:
        logger.error(f"Failed to reset configuration: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/config/llm")
async def get_llm_configuration():
    """
    Get current LLM configuration.

    Returns the active LLM provider settings based on the
    configured llm_provider field.

    Returns:
        Dict containing:
        - provider: Active provider name
        - base_url: Server URL (for Ollama)
        - model: Model name
        - api_key: Masked API key (for OpenAI)

    Raises:
        HTTPException: 500 if retrieval fails

    Example:
        ```python
        response = requests.get("/api/v1/config/llm")
        # Returns: {"provider": "ollama", "base_url": "...", "model": "llama2"}
        ```
    """
    try:
        llm_config = settings.get_llm_config()
        # Hide API key if present
        if "api_key" in llm_config and llm_config["api_key"]:
            llm_config["api_key"] = "***" + llm_config["api_key"][-4:]
        return llm_config
    except Exception as e:
        logger.error(f"Failed to get LLM configuration: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/config/test-llm")
async def test_llm_connection():
    """
    Test LLM connection with current settings.

    Verifies connectivity to the configured LLM provider:
    - For Ollama: Checks server availability and lists models
    - For OpenAI: Validates API key (not yet implemented)
    - For other providers: Returns not implemented status

    Returns:
        Dict containing:
        - status: Connection status (connected, error, not_implemented)
        - provider: Provider name
        - available_models: List of available models (Ollama only)
        - message: Error or status message

    Example:
        ```python
        response = requests.post("/api/v1/config/test-llm")
        # Success: {"status": "connected", "provider": "ollama", "available_models": [...]}
        # Failure: {"status": "error", "message": "Cannot connect to Ollama"}
        ```

    Note:
        This endpoint helps users verify their LLM configuration
        before attempting to use chat features.
    """
    try:
        llm_config = settings.get_llm_config()

        if llm_config["provider"] == "ollama":
            import httpx
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{llm_config['base_url']}/api/tags")
                if response.status_code == 200:
                    models = response.json().get("models", [])
                    return {
                        "status": "connected",
                        "provider": "ollama",
                        "available_models": [m["name"] for m in models]
                    }
                else:
                    return {"status": "error", "message": "Cannot connect to Ollama"}

        elif llm_config["provider"] == "openai":
            if not llm_config.get("api_key"):
                return {"status": "error", "message": "OpenAI API key not configured"}
            # Test OpenAI connection (would need actual implementation)
            return {"status": "not_implemented", "message": "OpenAI test not yet implemented"}

        else:
            return {"status": "error", "message": f"Unknown provider: {llm_config['provider']}"}

    except Exception as e:
        logger.error(f"LLM connection test failed: {str(e)}")
        return {"status": "error", "message": str(e)}