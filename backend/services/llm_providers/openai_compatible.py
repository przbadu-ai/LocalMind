"""OpenAI-compatible provider for generic LLM endpoints.

This provider works with any OpenAI-compatible API endpoint including:
- vLLM
- llama.cpp server
- Cerebras
- Mistral
- Any other OpenAI-compatible endpoint
"""

import asyncio
import json
import logging
import re
import time
from typing import Any, AsyncGenerator, Generator, Optional

from openai import AsyncOpenAI, OpenAI  # type: ignore

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
        self.async_client: Optional[AsyncOpenAI] = None
        self._init_client()

    def _init_client(self) -> None:
        """Initialize the OpenAI clients (sync and async)."""
        if self.base_url:
            self.client = OpenAI(
                base_url=self.base_url,
                api_key=self.api_key or "not-required",
            )
            self.async_client = AsyncOpenAI(
                base_url=self.base_url,
                api_key=self.api_key or "not-required",
            )
        else:
            self.client = None
            self.async_client = None

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

        logger.info(f"OpenAI-compatible request: model={self.model}, think={think}, tools={len(tools) if tools else 0}, base_url={self.base_url}")
        logger.debug(f"OpenAI-compatible request kwargs: {list(request_kwargs.keys())}")

        # Track timing for tokens/second calculation
        start_time = time.time()
        completion_tokens = 0
        prompt_tokens = 0

        try:
            stream = self.client.chat.completions.create(**request_kwargs)
        except Exception as e:
            error_str = str(e).lower()
            # Handle various provider-specific limitations

            # Check for tool choice issues (vLLM requires special server flags for tools)
            if ("tool choice" in error_str or
                "enable-auto-tool-choice" in error_str or
                "tool-call-parser" in error_str):
                logger.warning(f"Provider doesn't support tool calling, retrying without tools. Error: {e}")
                if "tools" in request_kwargs:
                    del request_kwargs["tools"]
                if "tool_choice" in request_kwargs:
                    del request_kwargs["tool_choice"]
                stream = self.client.chat.completions.create(**request_kwargs)
            # Check for stream_options issues
            elif ("stream_options" in error_str or
                  "unknown" in error_str or
                  "extra inputs" in error_str or
                  "validation error" in error_str):
                logger.warning(f"Provider may not support stream_options, retrying without it. Error: {e}")
                if "stream_options" in request_kwargs:
                    del request_kwargs["stream_options"]
                stream = self.client.chat.completions.create(**request_kwargs)
            # Generic 400 error - try removing both tools and stream_options
            elif "400" in error_str:
                logger.warning(f"Got 400 error, retrying without tools and stream_options. Error: {e}")
                if "tools" in request_kwargs:
                    del request_kwargs["tools"]
                if "tool_choice" in request_kwargs:
                    del request_kwargs["tool_choice"]
                if "stream_options" in request_kwargs:
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
                if not content:
                    continue

                if think:
                    # Add to buffer for tag detection
                    content_buffer += content
                    
                    # Estimate metrics
                    elapsed = time.time() - start_time
                    completion_tokens += int(len(content) / 4)
                    tps = completion_tokens / elapsed if elapsed > 0 else 0
                    partial_metrics = GenerationMetrics(
                        completion_tokens=completion_tokens,
                        tokens_per_second=round(tps, 2),
                        total_duration=round(elapsed, 2)
                    )

                    # Check for thinking start tag
                    if not in_thinking_block:
                        found_start, _, _ = self._detect_thinking_start(content_buffer)
                        if found_start:
                            # Extract content before start tag
                            for pattern in THINKING_START_PATTERNS:
                                match = re.search(pattern, content_buffer, re.IGNORECASE)
                                if match:
                                    before_content = content_buffer[:match.start()]
                                    if before_content:
                                        yield StreamChunk(type="content", content=before_content, metrics=partial_metrics)
                                    content_buffer = content_buffer[match.end():]
                                    in_thinking_block = True
                                    break
                        else:
                            # No thinking tag, yield content directly
                            yield StreamChunk(type="content", content=content_buffer, metrics=partial_metrics)
                            content_buffer = ""

                    # Check for thinking end tag (if in thinking block)
                    if in_thinking_block:
                        found_end, _, _ = self._detect_thinking_end(content_buffer)
                        if found_end:
                            # Extract thinking content before end tag
                            for pattern in THINKING_END_PATTERNS:
                                match = re.search(pattern, content_buffer, re.IGNORECASE)
                                if match:
                                    thinking_content = content_buffer[:match.start()]
                                    if thinking_content:
                                        yield StreamChunk(type="thinking", thinking=thinking_content, metrics=partial_metrics)
                                    content_buffer = content_buffer[match.end():]
                                    in_thinking_block = False
                                    break
                        elif len(content_buffer) > 100:
                            # Yield thinking content in chunks to avoid buffering too much
                            yield StreamChunk(type="thinking", thinking=content_buffer, metrics=partial_metrics)
                            content_buffer = ""
                else:
                    # Thinking detection disabled, yield as content directly
                    # Estimate metrics
                    elapsed = time.time() - start_time
                    completion_tokens += int(len(content) / 4)
                    tps = completion_tokens / elapsed if elapsed > 0 else 0
                    partial_metrics = GenerationMetrics(
                        completion_tokens=completion_tokens,
                        tokens_per_second=round(tps, 2),
                        total_duration=round(elapsed, 2)
                    )
                    yield StreamChunk(type="content", content=content, metrics=partial_metrics)

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
            think: Whether to enable thinking detection (default True)
        """
        if not self._ensure_client() or not self.async_client:
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
            "stream_options": {"include_usage": True},
        }
        if max_tokens:
            request_kwargs["max_tokens"] = max_tokens
        if tools:
            request_kwargs["tools"] = tools
            request_kwargs["tool_choice"] = "auto"

        logger.info(f"OpenAI-compatible async request: model={self.model}, think={think}, tools={len(tools) if tools else 0}, base_url={self.base_url}")

        # Track timing for tokens/second calculation
        start_time = time.time()
        completion_tokens = 0
        prompt_tokens = 0

        try:
            stream = await self.async_client.chat.completions.create(**request_kwargs)
        except Exception as e:
            error_str = str(e).lower()
            # Handle various provider-specific limitations
            if ("tool choice" in error_str or
                "enable-auto-tool-choice" in error_str or
                "tool-call-parser" in error_str):
                logger.warning(f"Provider doesn't support tool calling, retrying without tools. Error: {e}")
                if "tools" in request_kwargs:
                    del request_kwargs["tools"]
                if "tool_choice" in request_kwargs:
                    del request_kwargs["tool_choice"]
                stream = await self.async_client.chat.completions.create(**request_kwargs)
            elif ("stream_options" in error_str or
                  "unknown" in error_str or
                  "extra inputs" in error_str or
                  "validation error" in error_str):
                logger.warning(f"Provider may not support stream_options, retrying without it. Error: {e}")
                if "stream_options" in request_kwargs:
                    del request_kwargs["stream_options"]
                stream = await self.async_client.chat.completions.create(**request_kwargs)
            elif "400" in error_str:
                logger.warning(f"Got 400 error, retrying without tools and stream_options. Error: {e}")
                if "tools" in request_kwargs:
                    del request_kwargs["tools"]
                if "tool_choice" in request_kwargs:
                    del request_kwargs["tool_choice"]
                if "stream_options" in request_kwargs:
                    del request_kwargs["stream_options"]
                stream = await self.async_client.chat.completions.create(**request_kwargs)
            else:
                raise

        # Track tool calls being accumulated during streaming
        current_tool_calls: dict[int, dict[str, Any]] = {}

        # Track thinking state for tag-based detection
        in_thinking_block = False
        content_buffer = ""

        async for chunk in stream:
            # Handle usage stats
            if hasattr(chunk, 'usage') and chunk.usage:
                prompt_tokens = chunk.usage.prompt_tokens or 0
                completion_tokens = chunk.usage.completion_tokens or 0
                continue

            if not chunk.choices:
                continue

            delta = chunk.choices[0].delta

            # Handle content with thinking detection
            if delta.content:
                content = clean_llm_output(delta.content)
                if not content:
                    continue

                if think:
                    content_buffer += content
                    elapsed = time.time() - start_time
                    completion_tokens += int(len(content) / 4)
                    tps = completion_tokens / elapsed if elapsed > 0 else 0
                    partial_metrics = GenerationMetrics(
                        completion_tokens=completion_tokens,
                        tokens_per_second=round(tps, 2),
                        total_duration=round(elapsed, 2)
                    )

                    if not in_thinking_block:
                        found_start, _, _ = self._detect_thinking_start(content_buffer)
                        if found_start:
                            for pattern in THINKING_START_PATTERNS:
                                match = re.search(pattern, content_buffer, re.IGNORECASE)
                                if match:
                                    before_content = content_buffer[:match.start()]
                                    if before_content:
                                        yield StreamChunk(type="content", content=before_content, metrics=partial_metrics)
                                    content_buffer = content_buffer[match.end():]
                                    in_thinking_block = True
                                    break
                        else:
                            yield StreamChunk(type="content", content=content_buffer, metrics=partial_metrics)
                            content_buffer = ""

                    if in_thinking_block:
                        found_end, _, _ = self._detect_thinking_end(content_buffer)
                        if found_end:
                            for pattern in THINKING_END_PATTERNS:
                                match = re.search(pattern, content_buffer, re.IGNORECASE)
                                if match:
                                    thinking_content = content_buffer[:match.start()]
                                    if thinking_content:
                                        yield StreamChunk(type="thinking", thinking=thinking_content, metrics=partial_metrics)
                                    content_buffer = content_buffer[match.end():]
                                    in_thinking_block = False
                                    break
                        elif len(content_buffer) > 100:
                            yield StreamChunk(type="thinking", thinking=content_buffer, metrics=partial_metrics)
                            content_buffer = ""
                else:
                    elapsed = time.time() - start_time
                    completion_tokens += int(len(content) / 4)
                    tps = completion_tokens / elapsed if elapsed > 0 else 0
                    partial_metrics = GenerationMetrics(
                        completion_tokens=completion_tokens,
                        tokens_per_second=round(tps, 2),
                        total_duration=round(elapsed, 2)
                    )
                    yield StreamChunk(type="content", content=content, metrics=partial_metrics)

            # Handle tool calls
            if delta.tool_calls:
                for tool_call_delta in delta.tool_calls:
                    idx = tool_call_delta.index
                    if idx not in current_tool_calls:
                        current_tool_calls[idx] = {"id": "", "name": "", "arguments": ""}
                    if tool_call_delta.id:
                        current_tool_calls[idx]["id"] = tool_call_delta.id
                    if tool_call_delta.function:
                        if tool_call_delta.function.name:
                            current_tool_calls[idx]["name"] = tool_call_delta.function.name
                        if tool_call_delta.function.arguments:
                            current_tool_calls[idx]["arguments"] += tool_call_delta.function.arguments

            finish_reason = chunk.choices[0].finish_reason
            if finish_reason:
                logger.info(f"OpenAI-compatible async finish_reason: {finish_reason}")

            if finish_reason == "tool_calls":
                logger.info(f"OpenAI-compatible async requesting {len(current_tool_calls)} tool call(s)")
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
                        tool_call=ToolCall(id=tc["id"], name=tc["name"], arguments=args),
                    )
                current_tool_calls = {}

        # Flush remaining buffer
        if content_buffer:
            if in_thinking_block:
                yield StreamChunk(type="thinking", thinking=content_buffer)
            else:
                yield StreamChunk(type="content", content=content_buffer)

        # Calculate final metrics
        end_time = time.time()
        total_duration = end_time - start_time
        tokens_per_second = completion_tokens / total_duration if completion_tokens > 0 and total_duration > 0 else None
        metrics = GenerationMetrics(
            prompt_tokens=prompt_tokens if prompt_tokens else None,
            completion_tokens=completion_tokens if completion_tokens else None,
            total_tokens=(prompt_tokens + completion_tokens) if (prompt_tokens or completion_tokens) else None,
            total_duration=round(total_duration, 3) if total_duration else None,
            tokens_per_second=round(tokens_per_second, 2) if tokens_per_second else None,
        )
        if tokens_per_second:
            logger.info(f"OpenAI-compatible async metrics: {completion_tokens} tokens, {tokens_per_second:.2f} tok/s")
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
