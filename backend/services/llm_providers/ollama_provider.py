"""Native Ollama provider with thinking/reasoning support.

This provider uses the native ollama Python package to communicate with
Ollama servers, enabling full support for thinking/reasoning models like
deepseek-r1 and qwen3.
"""

import json
import logging
from typing import Any, Generator, Optional
from urllib.parse import urlparse

from .base import (
    BaseLLMProvider,
    ChatMessage,
    StreamChunk,
    ToolCall,
    clean_llm_output,
)

logger = logging.getLogger(__name__)

# Try to import ollama, handle gracefully if not installed
try:
    import ollama
    from ollama import Client
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False
    ollama = None
    Client = None


class OllamaProvider(BaseLLMProvider):
    """Provider for Ollama using the native ollama package.

    This provider supports:
    - Native thinking/reasoning output via `think=True`
    - Streaming with separate thinking and content chunks
    - Tool calling (if supported by the model)
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,  # Not used by Ollama but kept for interface compatibility
        model: Optional[str] = None,
    ):
        """Initialize the Ollama provider.

        Args:
            base_url: The Ollama server URL (e.g., http://localhost:11434)
            api_key: Not used by Ollama, kept for interface compatibility
            model: The model to use (e.g., deepseek-r1:7b, qwen3:8b)
        """
        super().__init__(base_url, api_key, model)
        self.client: Optional[Any] = None
        self._init_client()

    def _init_client(self) -> None:
        """Initialize the Ollama client."""
        if not OLLAMA_AVAILABLE:
            logger.warning("ollama package not installed. Run: pip install ollama")
            self.client = None
            return

        if self.base_url:
            # Parse the base_url to get just the host
            # Ollama package expects just the host URL without /v1 or /api paths
            parsed = urlparse(self.base_url)
            host = f"{parsed.scheme}://{parsed.netloc}"
            self.client = Client(host=host)
        else:
            # Use default localhost
            self.client = Client()

    def _ensure_client(self) -> bool:
        """Ensure the client is initialized.

        Returns:
            True if client is ready
        """
        if not OLLAMA_AVAILABLE:
            return False

        if self.client is not None:
            return True

        self._init_client()
        return self.client is not None

    def _format_messages(self, messages: list[ChatMessage]) -> list[dict[str, Any]]:
        """Format ChatMessage list to Ollama format.

        Args:
            messages: List of ChatMessage objects

        Returns:
            List of message dicts in Ollama format
        """
        formatted = []
        for msg in messages:
            formatted_msg: dict[str, Any] = {"role": msg.role}

            # Handle multimodal content
            if isinstance(msg.content, list):
                # Extract text and images
                text_parts = []
                images = []
                for block in msg.content:
                    if block.get("type") == "text":
                        text_parts.append(block.get("text", ""))
                    elif block.get("type") == "image_url":
                        # Extract base64 data from data URL
                        image_url = block.get("image_url", {}).get("url", "")
                        if image_url.startswith("data:"):
                            # Extract base64 part after the comma
                            _, base64_data = image_url.split(",", 1)
                            images.append(base64_data)
                        else:
                            images.append(image_url)

                formatted_msg["content"] = " ".join(text_parts)
                if images:
                    formatted_msg["images"] = images
            else:
                formatted_msg["content"] = msg.content

            formatted.append(formatted_msg)

        return formatted

    def chat(
        self,
        messages: list[ChatMessage],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> str:
        """Send a chat completion request and return the response."""
        if not self._ensure_client():
            raise RuntimeError(
                "Ollama not available. Please install: pip install ollama"
            )

        formatted_messages = self._format_messages(messages)

        options: dict[str, Any] = {"temperature": temperature}
        if max_tokens:
            options["num_predict"] = max_tokens

        try:
            response = self.client.chat(
                model=self.model,
                messages=formatted_messages,
                options=options,
            )

            content = response.get("message", {}).get("content", "")
            return clean_llm_output(content)

        except Exception as e:
            logger.error(f"Ollama chat error: {e}")
            raise RuntimeError(f"Ollama chat failed: {e}")

    def chat_stream(
        self,
        messages: list[ChatMessage],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        tools: Optional[list[dict[str, Any]]] = None,
        think: bool = True,
    ) -> Generator[StreamChunk, None, None]:
        """Send a chat completion request and stream the response.

        When think=True, this will yield both thinking and content chunks
        separately, allowing the frontend to display reasoning in a
        collapsible section.

        Args:
            messages: List of chat messages
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            tools: Optional list of tool definitions (Ollama tool support)
            think: Whether to enable thinking/reasoning output

        Yields:
            StreamChunk objects with type "thinking", "content", "tool_call", or "done"
        """
        if not self._ensure_client():
            raise RuntimeError(
                "Ollama not available. Please install: pip install ollama"
            )

        formatted_messages = self._format_messages(messages)

        options: dict[str, Any] = {"temperature": temperature}
        if max_tokens:
            options["num_predict"] = max_tokens

        # Build request kwargs
        request_kwargs: dict[str, Any] = {
            "model": self.model,
            "messages": formatted_messages,
            "stream": True,
            "options": options,
        }

        # Enable thinking if requested
        # This tells Ollama to return thinking content separately
        if think:
            request_kwargs["think"] = True

        # Add tools if provided
        if tools:
            request_kwargs["tools"] = tools

        logger.info(f"Ollama streaming request: model={self.model}, think={think}, tools={len(tools) if tools else 0}")

        try:
            stream = self.client.chat(**request_kwargs)

            # Track accumulated content for tool call parsing
            current_tool_calls: dict[int, dict[str, Any]] = {}

            for chunk in stream:
                message = chunk.get("message", {})

                # Handle thinking content (separate from main content)
                thinking = message.get("thinking")
                if thinking:
                    cleaned_thinking = clean_llm_output(thinking)
                    if cleaned_thinking:
                        yield StreamChunk(type="thinking", thinking=cleaned_thinking)

                # Handle main content
                content = message.get("content")
                if content:
                    cleaned_content = clean_llm_output(content)
                    if cleaned_content:
                        yield StreamChunk(type="content", content=cleaned_content)

                # Handle tool calls
                tool_calls = message.get("tool_calls")
                if tool_calls:
                    for i, tc in enumerate(tool_calls):
                        func = tc.get("function", {})
                        tool_call = ToolCall(
                            id=tc.get("id", f"call_{i}"),
                            name=func.get("name", ""),
                            arguments=func.get("arguments", {}),
                        )
                        yield StreamChunk(type="tool_call", tool_call=tool_call)

                # Check if done
                if chunk.get("done"):
                    break

            # Signal completion
            yield StreamChunk(type="done")

        except Exception as e:
            logger.error(f"Ollama streaming error: {e}")
            raise RuntimeError(f"Ollama streaming failed: {e}")

    def is_available(self) -> bool:
        """Check if Ollama is available."""
        if not self._ensure_client():
            return False

        try:
            # Try to list models as a health check
            self.client.list()
            return True
        except Exception:
            return False

    def get_models(self) -> list[str]:
        """Get list of available models from Ollama."""
        if not self._ensure_client():
            return []

        try:
            response = self.client.list()
            models = response.get("models", [])
            return [m.get("name", "") for m in models if m.get("name")]
        except Exception as e:
            logger.error(f"Failed to get Ollama models: {e}")
            return []

    def update_config(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
    ) -> None:
        """Update the provider configuration."""
        super().update_config(base_url, api_key, model)
        # Reinitialize client with new settings
        self._init_client()
