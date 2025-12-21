"""LLM service for OpenAI-compatible endpoints."""

import json
import logging
from typing import Any, Generator, Optional, Union

from openai import OpenAI # type: ignore
from pydantic import BaseModel # type: ignore

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
    """A chunk from the streaming response."""

    type: str  # "content", "tool_call", "done"
    content: Optional[str] = None
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
    """Service for interacting with OpenAI-compatible LLM endpoints."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
    ):
        # If no explicit values provided, try to load from database
        if base_url is None or api_key is None or model is None:
            db_config = _get_llm_config_from_db()
            self.base_url = base_url or db_config.get("base_url", "")
            self.api_key = api_key or db_config.get("api_key", "not-required")
            self.model = model or db_config.get("model", "")
        else:
            self.base_url = base_url
            self.api_key = api_key
            self.model = model

        # Only create client if we have a base_url
        if self.base_url:
            self.client = OpenAI(
                base_url=self.base_url,
                api_key=self.api_key or "not-required",
            )
        else:
            self.client = None

    def _ensure_client(self) -> bool:
        """Ensure the client is initialized. Returns True if ready."""
        if self.client is not None:
            return True

        # Try to reload config from database
        db_config = _get_llm_config_from_db()
        if db_config.get("base_url"):
            self.base_url = db_config.get("base_url", "")
            self.api_key = db_config.get("api_key", "not-required")
            self.model = db_config.get("model", "")
            self.client = OpenAI(
                base_url=self.base_url,
                api_key=self.api_key or "not-required",
            )
            return True

        return False

    def chat(
        self,
        messages: list[ChatMessage],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> str:
        """Send a chat completion request and return the response."""
        if not self._ensure_client():
            raise RuntimeError("LLM not configured. Please configure LLM settings first.")

        formatted_messages = [
            {"role": msg.role, "content": msg.content} for msg in messages
        ]

        response = self.client.chat.completions.create(
            model=self.model,
            messages=formatted_messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        content = response.choices[0].message.content or ""
        return clean_llm_output(content)

    def chat_stream(
        self,
        messages: list[ChatMessage],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        tools: Optional[list[dict[str, Any]]] = None,
    ) -> Generator[StreamChunk, None, None]:
        """Send a chat completion request and stream the response.

        When tools are provided, yields StreamChunk objects that can contain
        either content or tool calls.
        """
        if not self._ensure_client():
            raise RuntimeError("LLM not configured. Please configure LLM settings first.")

        formatted_messages = []
        for msg in messages:
            formatted_msg: dict[str, Any] = {"role": msg.role, "content": msg.content}
            if msg.tool_calls:
                formatted_msg["tool_calls"] = msg.tool_calls
            if msg.tool_call_id:
                formatted_msg["tool_call_id"] = msg.tool_call_id
            formatted_messages.append(formatted_msg)

        # Build request kwargs
        request_kwargs: dict[str, Any] = {
            "model": self.model,
            "messages": formatted_messages,
            "temperature": temperature,
            "stream": True,
        }
        if max_tokens:
            request_kwargs["max_tokens"] = max_tokens
        if tools:
            request_kwargs["tools"] = tools
            request_kwargs["tool_choice"] = "auto"  # Enable automatic tool selection

        logger.info(f"LLM request: model={self.model}, tools={len(tools) if tools else 0}")
        stream = self.client.chat.completions.create(**request_kwargs)

        # Track tool calls being accumulated during streaming
        current_tool_calls: dict[int, dict[str, Any]] = {}

        for chunk in stream:
            if not chunk.choices:
                continue

            delta = chunk.choices[0].delta

            # Handle content
            if delta.content:
                content = clean_llm_output(delta.content)
                if content:
                    yield StreamChunk(type="content", content=content)

            # Handle tool calls
            if delta.tool_calls:
                for tool_call_delta in delta.tool_calls:
                    idx = tool_call_delta.index

                    # Initialize new tool call
                    if idx not in current_tool_calls:
                        current_tool_calls[idx] = {
                            "id": "",
                            "name": "",
                            "arguments": "",
                        }

                    # Accumulate tool call data
                    if tool_call_delta.id:
                        current_tool_calls[idx]["id"] = tool_call_delta.id
                    if tool_call_delta.function:
                        if tool_call_delta.function.name:
                            current_tool_calls[idx]["name"] = tool_call_delta.function.name
                        if tool_call_delta.function.arguments:
                            current_tool_calls[idx]["arguments"] += tool_call_delta.function.arguments

            # Check for finish reason
            finish_reason = chunk.choices[0].finish_reason
            if finish_reason:
                logger.info(f"LLM finish_reason: {finish_reason}")

            if finish_reason == "tool_calls":
                # Yield all accumulated tool calls
                logger.info(f"LLM requesting {len(current_tool_calls)} tool call(s)")
                for idx in sorted(current_tool_calls.keys()):
                    tc = current_tool_calls[idx]
                    try:
                        args = json.loads(tc["arguments"]) if tc["arguments"] else {}
                    except json.JSONDecodeError:
                        logger.warning(f"Failed to parse tool arguments: {tc['arguments']}")
                        args = {}

                    logger.info(f"  Tool call: {tc['name']} with args: {args}")
                    yield StreamChunk(
                        type="tool_call",
                        tool_call=ToolCall(
                            id=tc["id"],
                            name=tc["name"],
                            arguments=args,
                        ),
                    )
                current_tool_calls = {}

        # Signal completion
        yield StreamChunk(type="done")

    def chat_stream_simple(
        self,
        messages: list[ChatMessage],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> Generator[str, None, None]:
        """Simple streaming without tool support - yields content strings only."""
        for chunk in self.chat_stream(messages, temperature, max_tokens, tools=None):
            if chunk.type == "content" and chunk.content:
                yield chunk.content

    def is_available(self) -> bool:
        """Check if the LLM endpoint is available."""
        if not self._ensure_client():
            return False

        try:
            # Try to list models as a health check
            self.client.models.list()
            return True
        except Exception:
            return False

    def get_models(self) -> list[str]:
        """Get list of available models."""
        if not self._ensure_client():
            return []

        try:
            models = self.client.models.list()
            return [model.id for model in models.data]
        except Exception:
            return []

    def update_config(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
    ) -> None:
        """Update the LLM configuration."""
        if base_url:
            self.base_url = base_url
        if api_key:
            self.api_key = api_key
        if model:
            self.model = model

        # Recreate the client with new settings
        if self.base_url:
            self.client = OpenAI(
                base_url=self.base_url,
                api_key=self.api_key or "not-required",
            )
        else:
            self.client = None


# Global LLM service instance
llm_service = LLMService()
