"""OpenAI-compatible provider for generic LLM endpoints.

This provider works with any OpenAI-compatible API endpoint including:
- vLLM
- llama.cpp server
- Cerebras
- Mistral
- Any other OpenAI-compatible endpoint
"""

import json
import logging
from typing import Any, Generator, Optional

from openai import OpenAI

from .base import (
    BaseLLMProvider,
    ChatMessage,
    StreamChunk,
    ToolCall,
    clean_llm_output,
)

logger = logging.getLogger(__name__)


class OpenAICompatibleProvider(BaseLLMProvider):
    """Provider for OpenAI-compatible API endpoints."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
    ):
        """Initialize the OpenAI-compatible provider.

        Args:
            base_url: The API base URL (e.g., http://localhost:8000/v1)
            api_key: The API key (if required)
            model: The model to use
        """
        super().__init__(base_url, api_key, model)
        self.client: Optional[OpenAI] = None
        self._init_client()

    def _init_client(self) -> None:
        """Initialize the OpenAI client."""
        if self.base_url:
            self.client = OpenAI(
                base_url=self.base_url,
                api_key=self.api_key or "not-required",
            )
        else:
            self.client = None

    def _ensure_client(self) -> bool:
        """Ensure the client is initialized.

        Returns:
            True if client is ready
        """
        if self.client is not None:
            return True

        if self.base_url:
            self._init_client()
            return self.client is not None

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
        think: bool = True,
    ) -> Generator[StreamChunk, None, None]:
        """Send a chat completion request and stream the response.

        Note: OpenAI-compatible endpoints generally don't support native thinking,
        so the `think` parameter is accepted but may not have any effect unless
        the endpoint specifically supports it.
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
            request_kwargs["tool_choice"] = "auto"

        logger.info(f"OpenAI-compatible request: model={self.model}, tools={len(tools) if tools else 0}")
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
                logger.info(f"OpenAI-compatible finish_reason: {finish_reason}")

            if finish_reason == "tool_calls":
                # Yield all accumulated tool calls
                logger.info(f"OpenAI-compatible requesting {len(current_tool_calls)} tool call(s)")
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

    def is_available(self) -> bool:
        """Check if the provider is available."""
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
        """Update the provider configuration."""
        super().update_config(base_url, api_key, model)
        # Reinitialize client with new settings
        self._init_client()
