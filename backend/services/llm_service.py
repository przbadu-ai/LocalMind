"""LLM service with provider factory pattern.

This service supports multiple LLM providers using native packages:
- Ollama: Native ollama package with thinking support
- OpenAI: Native openai package
- Others: OpenAI-compatible API (vLLM, llama.cpp, Cerebras, Mistral)
"""

import logging
from typing import Any, AsyncGenerator, Generator, Optional

from .llm_providers import (
    BaseLLMProvider,
    ChatMessage,
    StreamChunk,
    ToolCall,
    MultimodalContent,
    ContentBlock,
    clean_llm_output,
    OpenAICompatibleProvider,
    OllamaProvider,
)

logger = logging.getLogger(__name__)

# Re-export types for backward compatibility
__all__ = [
    "LLMService",
    "ChatMessage",
    "StreamChunk",
    "ToolCall",
    "MultimodalContent",
    "ContentBlock",
    "clean_llm_output",
    "llm_service",
    "get_provider",
]

# Provider name to class mapping
PROVIDER_CLASSES = {
    "ollama": OllamaProvider,
    # OpenAI-compatible providers (use generic implementation)
    "openai": OpenAICompatibleProvider,
    "cerebras": OpenAICompatibleProvider,
    "mistral": OpenAICompatibleProvider,
    "claude": OpenAICompatibleProvider,  # Anthropic's OpenAI-compatible endpoint
    "gemini": OpenAICompatibleProvider,  # Google's OpenAI-compatible endpoint
    "openai_compatible": OpenAICompatibleProvider,
}


def get_provider(
    provider_name: str,
    base_url: str,
    api_key: Optional[str] = None,
    model: Optional[str] = None,
) -> BaseLLMProvider:
    """Factory function to create the appropriate provider instance.

    Args:
        provider_name: Name of the provider (ollama, openai, cerebras, etc.)
        base_url: The API base URL
        api_key: The API key (if required)
        model: The model to use

    Returns:
        An instance of the appropriate provider class
    """
    provider_class = PROVIDER_CLASSES.get(provider_name.lower(), OpenAICompatibleProvider)
    return provider_class(base_url=base_url, api_key=api_key, model=model)


def _get_llm_config_from_db() -> dict:
    """Get LLM configuration from the database (llm_providers table)."""
    try:
        from database.repositories.config_repository import ConfigRepository
        config_repo = ConfigRepository()

        # Get default provider with decrypted API key
        default_provider = config_repo.get_default_llm_provider_for_use()
        if default_provider:
            return {
                "provider": default_provider.name,
                "base_url": default_provider.base_url,
                "api_key": default_provider.api_key or "",
                "model": default_provider.model or "",
            }

        return {}
    except Exception:
        # Database might not be initialized yet
        return {}


class LLMService:
    """Service for interacting with LLM providers.

    This service uses a factory pattern to instantiate the correct provider
    based on the provider name. It maintains backward compatibility with
    the previous interface while adding support for native provider features
    like Ollama's thinking output.
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        provider_name: Optional[str] = None,
    ):
        """Initialize the LLM service.

        Args:
            base_url: The API base URL
            api_key: The API key (if required)
            model: The model to use
            provider_name: Name of the provider (auto-detected if not provided)
        """
        # If no explicit values provided, try to load from database
        if base_url is None or model is None:
            db_config = _get_llm_config_from_db()
            self.base_url = base_url or db_config.get("base_url", "")
            self.api_key = api_key or db_config.get("api_key", "not-required")
            self.model = model or db_config.get("model", "")
            self._provider_name = provider_name or db_config.get("provider", "openai_compatible")
        else:
            self.base_url = base_url
            self.api_key = api_key or "not-required"
            self.model = model or ""
            self._provider_name = provider_name or self._detect_provider(base_url)

        # Create the appropriate provider
        self._provider: Optional[BaseLLMProvider] = None
        self._init_provider()

    def _detect_provider(self, base_url: str) -> str:
        """Detect provider from base URL.

        Args:
            base_url: The API base URL

        Returns:
            Detected provider name
        """
        if not base_url:
            return "openai_compatible"

        base_url_lower = base_url.lower()

        # Check for known provider URLs
        if "11434" in base_url_lower or "ollama" in base_url_lower:
            return "ollama"
        elif "api.openai.com" in base_url_lower:
            return "openai"
        elif "api.anthropic.com" in base_url_lower:
            return "claude"
        elif "generativelanguage.googleapis.com" in base_url_lower:
            return "gemini"
        elif "cerebras" in base_url_lower:
            return "cerebras"
        elif "mistral" in base_url_lower:
            return "mistral"

        return "openai_compatible"

    def _init_provider(self) -> None:
        """Initialize the provider instance."""
        if self.base_url:
            self._provider = get_provider(
                provider_name=self._provider_name,
                base_url=self.base_url,
                api_key=self.api_key,
                model=self.model,
            )
        else:
            self._provider = None

    def _ensure_provider(self) -> bool:
        """Ensure the provider is initialized.

        Returns:
            True if provider is ready
        """
        if self._provider is not None:
            return True

        # Try to reload config from database
        db_config = _get_llm_config_from_db()
        if db_config.get("base_url"):
            self.base_url = db_config.get("base_url", "")
            self.api_key = db_config.get("api_key", "not-required")
            self.model = db_config.get("model", "")
            self._provider_name = db_config.get("provider", "openai_compatible")
            self._init_provider()
            return self._provider is not None

        return False

    @property
    def provider_name(self) -> str:
        """Get the current provider name."""
        return self._provider_name

    def chat(
        self,
        messages: list[ChatMessage],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> str:
        """Send a chat completion request and return the response.

        Args:
            messages: List of chat messages
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate

        Returns:
            The generated response text
        """
        if not self._ensure_provider():
            raise RuntimeError("LLM not configured. Please configure LLM settings first.")

        return self._provider.chat(messages, temperature, max_tokens)

    def chat_stream(
        self,
        messages: list[ChatMessage],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        tools: Optional[list[dict[str, Any]]] = None,
        think: bool = True,
    ) -> Generator[StreamChunk, None, None]:
        """Send a chat completion request and stream the response.

        When using providers that support thinking (like Ollama with deepseek-r1),
        this will yield both thinking and content chunks separately.

        Args:
            messages: List of chat messages
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            tools: Optional list of tool definitions
            think: Whether to enable thinking/reasoning output

        Yields:
            StreamChunk objects containing content, thinking, or tool calls
        """
        if not self._ensure_provider():
            raise RuntimeError("LLM not configured. Please configure LLM settings first.")

        yield from self._provider.chat_stream(messages, temperature, max_tokens, tools, think)

    async def chat_stream_async(
        self,
        messages: list[ChatMessage],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        tools: Optional[list[dict[str, Any]]] = None,
        think: bool = True,
    ) -> AsyncGenerator[StreamChunk, None]:
        """Async version of chat_stream for concurrent request handling.

        Args:
            messages: List of chat messages
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            tools: Optional list of tool definitions
            think: Whether to enable thinking/reasoning output

        Yields:
            StreamChunk objects containing content, thinking, or tool calls
        """
        if not self._ensure_provider():
            raise RuntimeError("LLM not configured. Please configure LLM settings first.")

        # Use async method if available, otherwise fall back to sync with warning
        if hasattr(self._provider, 'chat_stream_async'):
            async for chunk in self._provider.chat_stream_async(messages, temperature, max_tokens, tools, think):
                yield chunk
        else:
            # Fall back to sync for providers that don't support async yet
            logger.warning(f"Provider {type(self._provider).__name__} doesn't support async streaming, using sync")
            for chunk in self._provider.chat_stream(messages, temperature, max_tokens, tools, think):
                yield chunk

    def chat_stream_simple(
        self,
        messages: list[ChatMessage],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> Generator[str, None, None]:
        """Simple streaming without tool support - yields content strings only.

        Args:
            messages: List of chat messages
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate

        Yields:
            Content strings
        """
        for chunk in self.chat_stream(messages, temperature, max_tokens, tools=None, think=False):
            if chunk.type == "content" and chunk.content:
                yield chunk.content

    def is_available(self) -> bool:
        """Check if the LLM endpoint is available.

        Returns:
            True if the provider can accept requests
        """
        if not self._ensure_provider():
            return False

        return self._provider.is_available()

    def get_models(self) -> list[str]:
        """Get list of available models.

        Returns:
            List of model identifiers
        """
        if not self._ensure_provider():
            return []

        return self._provider.get_models()

    def update_config(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        provider_name: Optional[str] = None,
    ) -> None:
        """Update the LLM configuration.

        Args:
            base_url: New base URL
            api_key: New API key
            model: New model
            provider_name: New provider name
        """
        if base_url:
            self.base_url = base_url
        if api_key:
            self.api_key = api_key
        if model:
            self.model = model
        if provider_name:
            self._provider_name = provider_name
        elif base_url:
            # Re-detect provider if base_url changed
            self._provider_name = self._detect_provider(base_url)

        # Recreate the provider with new settings
        self._init_provider()


# Global LLM service instance
llm_service = LLMService()
