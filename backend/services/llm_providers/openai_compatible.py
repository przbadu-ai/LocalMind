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
import re
import time
from typing import Any, Generator, Optional

from openai import OpenAI  # type: ignore

from .base import (
    BaseLLMProvider,
    ChatMessage,
    GenerationMetrics,
    StreamChunk,
    ToolCall,
    clean_llm_output,
)

# Patterns that indicate thinking/reasoning content in streamed responses
THINKING_START_PATTERNS = [
    r"<think>",
    r"<thinking>",
    r"<\|begin_of_thought\|>",
    r"<reasoning>",
]
THINKING_END_PATTERNS = [
    r"</think>",
    r"</thinking>",
    r"<\|end_of_thought\|>",
    r"</reasoning>",
]

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

    def _detect_thinking_start(self, text: str) -> tuple[bool, str, str]:
        """Check if text contains a thinking start tag.

        Returns:
            Tuple of (found, tag, remaining_text_after_tag)
        """
        for pattern in THINKING_START_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return True, match.group(), text[match.end():]
        return False, "", text

    def _detect_thinking_end(self, text: str) -> tuple[bool, str, str]:
        """Check if text contains a thinking end tag.

        Returns:
            Tuple of (found, tag, remaining_text_after_tag)
        """
        for pattern in THINKING_END_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return True, match.group(), text[match.end():]
        return False, "", text

    def chat_stream(
        self,
        messages: list[ChatMessage],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        tools: Optional[list[dict[str, Any]]] = None,
        think: bool = True,
    ) -> Generator[StreamChunk, None, None]:
        """Send a chat completion request and stream the response.

        This provider detects thinking/reasoning content in streamed responses
        by looking for common thinking tags (<think>, <thinking>, etc.) and
        yields them as separate thinking chunks.

        Args:
            messages: List of chat messages
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            tools: Optional list of tool definitions
            think: Whether to enable thinking detection (default True)
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
            # Request usage stats in streaming mode (OpenAI API feature)
            "stream_options": {"include_usage": True},
        }
        if max_tokens:
            request_kwargs["max_tokens"] = max_tokens
        if tools:
            request_kwargs["tools"] = tools
            request_kwargs["tool_choice"] = "auto"

        logger.info(f"OpenAI-compatible request: model={self.model}, think={think}, tools={len(tools) if tools else 0}")

        # Track timing for tokens/second calculation
        start_time = time.time()
        completion_tokens = 0
        prompt_tokens = 0

        try:
            stream = self.client.chat.completions.create(**request_kwargs)
        except Exception as e:
            # Some providers don't support stream_options, retry without it
            if "stream_options" in str(e).lower() or "unknown" in str(e).lower():
                logger.warning("Provider doesn't support stream_options, retrying without usage tracking")
                del request_kwargs["stream_options"]
                stream = self.client.chat.completions.create(**request_kwargs)
            else:
                raise

        # Track tool calls being accumulated during streaming
        current_tool_calls: dict[int, dict[str, Any]] = {}

        # Track thinking state for tag-based detection
        in_thinking_block = False
        content_buffer = ""

        for chunk in stream:
            # Handle usage stats (OpenAI sends this in a separate final chunk)
            if hasattr(chunk, 'usage') and chunk.usage:
                prompt_tokens = chunk.usage.prompt_tokens or 0
                completion_tokens = chunk.usage.completion_tokens or 0
                continue  # Usage chunk has no choices

            if not chunk.choices:
                continue

            delta = chunk.choices[0].delta

            # Handle content with thinking detection
            if delta.content:
                content = clean_llm_output(delta.content)
                if content and think:
                    # Add to buffer for tag detection
                    content_buffer += content

                    # Process buffer for thinking tags
                    while content_buffer:
                        if in_thinking_block:
                            # Look for end tag
                            found_end, _, remaining = self._detect_thinking_end(content_buffer)
                            if found_end:
                                # Extract thinking content before end tag
                                end_match = None
                                for pattern in THINKING_END_PATTERNS:
                                    end_match = re.search(pattern, content_buffer, re.IGNORECASE)
                                    if end_match:
                                        break
                                if end_match:
                                    thinking_content = content_buffer[:end_match.start()]
                                    if thinking_content:
                                        yield StreamChunk(type="thinking", thinking=thinking_content)
                                    content_buffer = content_buffer[end_match.end():]
                                    in_thinking_block = False
                            else:
                                # Still in thinking block, yield what we have and wait for more
                                if len(content_buffer) > 50:  # Yield in chunks to avoid buffering too much
                                    yield StreamChunk(type="thinking", thinking=content_buffer)
                                    content_buffer = ""
                                break
                        else:
                            # Look for start tag
                            found_start, _, _ = self._detect_thinking_start(content_buffer)
                            if found_start:
                                # Extract content before start tag
                                start_match = None
                                for pattern in THINKING_START_PATTERNS:
                                    start_match = re.search(pattern, content_buffer, re.IGNORECASE)
                                    if start_match:
                                        break
                                if start_match:
                                    before_content = content_buffer[:start_match.start()]
                                    if before_content:
                                        yield StreamChunk(type="content", content=before_content)
                                    content_buffer = content_buffer[start_match.end():]
                                    in_thinking_block = True
                            else:
                                # No thinking tag found, yield as content
                                yield StreamChunk(type="content", content=content_buffer)
                                content_buffer = ""
                                break
                elif content:
                    # Thinking detection disabled, yield as content directly
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

        # Flush any remaining buffer
        if content_buffer:
            if in_thinking_block:
                yield StreamChunk(type="thinking", thinking=content_buffer)
            else:
                yield StreamChunk(type="content", content=content_buffer)

        # Calculate metrics
        end_time = time.time()
        total_duration = end_time - start_time

        # Calculate tokens per second
        tokens_per_second = None
        if completion_tokens > 0 and total_duration > 0:
            tokens_per_second = completion_tokens / total_duration

        metrics = GenerationMetrics(
            prompt_tokens=prompt_tokens if prompt_tokens else None,
            completion_tokens=completion_tokens if completion_tokens else None,
            total_tokens=(prompt_tokens + completion_tokens) if (prompt_tokens or completion_tokens) else None,
            total_duration=round(total_duration, 3) if total_duration else None,
            tokens_per_second=round(tokens_per_second, 2) if tokens_per_second else None,
        )

        if tokens_per_second:
            logger.info(f"OpenAI-compatible metrics: {completion_tokens} tokens, {tokens_per_second:.2f} tok/s")

        # Signal completion with metrics
        yield StreamChunk(type="done", metrics=metrics)

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
