"""LLM service for OpenAI-compatible endpoints."""

from typing import Generator, Optional

from openai import OpenAI
from pydantic import BaseModel


class ChatMessage(BaseModel):
    """A single chat message."""

    role: str
    content: str


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
    """Get LLM configuration from the database."""
    try:
        from database.repositories.config_repository import ConfigRepository
        config_repo = ConfigRepository()
        return config_repo.get_config_value("llm", {})
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
    ) -> Generator[str, None, None]:
        """Send a chat completion request and stream the response."""
        if not self._ensure_client():
            raise RuntimeError("LLM not configured. Please configure LLM settings first.")

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
                content = clean_llm_output(chunk.choices[0].delta.content)
                if content:  # Only yield non-empty content
                    yield content

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
