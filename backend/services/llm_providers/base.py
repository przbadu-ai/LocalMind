"""Base class for LLM providers."""

import logging
from abc import ABC, abstractmethod
from typing import Any, Generator, Optional, Union

from pydantic import BaseModel

logger = logging.getLogger(__name__)


# Type alias for multimodal content (text + images)
ContentBlock = dict[str, Any]
MultimodalContent = Union[str, list[ContentBlock]]


class ChatMessage(BaseModel):
    """A single chat message.

    Content can be either:
    - A simple string for text-only messages
    - A list of content blocks for multimodal messages (text + images)

    Example multimodal content:
    [
        {"type": "text", "text": "What's in this image?"},
        {"type": "image_url", "image_url": {"url": "data:image/png;base64,..."}}
    ]
    """

    role: str
    content: MultimodalContent
    tool_calls: Optional[list[dict[str, Any]]] = None
    tool_call_id: Optional[str] = None


class ToolCall(BaseModel):
    """Represents a tool call from the LLM."""

    id: str
    name: str
    arguments: dict[str, Any]


class StreamChunk(BaseModel):
    """A chunk from the streaming response.

    Types:
    - "content": Regular response content
    - "thinking": Reasoning/thinking content from models like deepseek-r1, qwen3
    - "tool_call": Tool/function call request
    - "done": Stream completion signal
    """

    type: str  # "content", "thinking", "tool_call", "done"
    content: Optional[str] = None
    thinking: Optional[str] = None  # Reasoning/thinking content
    tool_call: Optional[ToolCall] = None


# Special tokens that should be filtered from LLM output
SPECIAL_TOKENS = [
    "<|im_start|>",
    "<|im_end|>",
    "<|endoftext|>",
    "<|assistant|>",
    "<|user|>",
    "<|system|>",
]


def clean_llm_output(text: str) -> str:
    """Remove special tokens from LLM output."""
    for token in SPECIAL_TOKENS:
        text = text.replace(token, "")
    return text


class BaseLLMProvider(ABC):
    """Abstract base class for LLM providers.

    All provider implementations must inherit from this class and implement
    the abstract methods.
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
    ):
        """Initialize the provider.

        Args:
            base_url: The API base URL
            api_key: The API key (if required)
            model: The model to use
        """
        self.base_url = base_url or ""
        self.api_key = api_key or ""
        self.model = model or ""

    @abstractmethod
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
        pass

    @abstractmethod
    def chat_stream(
        self,
        messages: list[ChatMessage],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        tools: Optional[list[dict[str, Any]]] = None,
        think: bool = True,
    ) -> Generator[StreamChunk, None, None]:
        """Send a chat completion request and stream the response.

        Args:
            messages: List of chat messages
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            tools: Optional list of tool definitions
            think: Whether to enable thinking/reasoning output

        Yields:
            StreamChunk objects containing content, thinking, or tool calls
        """
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if the provider is available and configured.

        Returns:
            True if the provider can accept requests
        """
        pass

    @abstractmethod
    def get_models(self) -> list[str]:
        """Get list of available models from this provider.

        Returns:
            List of model identifiers
        """
        pass

    def update_config(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
    ) -> None:
        """Update the provider configuration.

        Args:
            base_url: New base URL
            api_key: New API key
            model: New model
        """
        if base_url:
            self.base_url = base_url
        if api_key:
            self.api_key = api_key
        if model:
            self.model = model

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
