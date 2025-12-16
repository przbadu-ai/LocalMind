"""LLM service for OpenAI-compatible endpoints."""

from typing import Generator, Optional

from openai import OpenAI
from pydantic import BaseModel

from backend.config import settings


class ChatMessage(BaseModel):
    """A single chat message."""

    role: str
    content: str


class LLMService:
    """Service for interacting with OpenAI-compatible LLM endpoints."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
    ):
        self.base_url = base_url or settings.llm_base_url
        self.api_key = api_key or settings.llm_api_key
        self.model = model or settings.llm_model

        self.client = OpenAI(
            base_url=self.base_url,
            api_key=self.api_key,
        )

    def chat(
        self,
        messages: list[ChatMessage],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> str:
        """Send a chat completion request and return the response."""
        formatted_messages = [
            {"role": msg.role, "content": msg.content} for msg in messages
        ]

        response = self.client.chat.completions.create(
            model=self.model,
            messages=formatted_messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        return response.choices[0].message.content or ""

    def chat_stream(
        self,
        messages: list[ChatMessage],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> Generator[str, None, None]:
        """Send a chat completion request and stream the response."""
        formatted_messages = [
            {"role": msg.role, "content": msg.content} for msg in messages
        ]

        stream = self.client.chat.completions.create(
            model=self.model,
            messages=formatted_messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True,
        )

        for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    def is_available(self) -> bool:
        """Check if the LLM endpoint is available."""
        try:
            # Try to list models as a health check
            self.client.models.list()
            return True
        except Exception:
            return False

    def get_models(self) -> list[str]:
        """Get list of available models."""
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
        self.client = OpenAI(
            base_url=self.base_url,
            api_key=self.api_key,
        )


# Global LLM service instance
llm_service = LLMService()
