"""Pydantic models for database entities."""

import uuid
from datetime import datetime
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field


def generate_uuid() -> str:
    """Generate a new UUID string."""
    return str(uuid.uuid4())


class Chat(BaseModel):
    """Chat conversation model."""

    id: str = Field(default_factory=generate_uuid)
    title: str = "New Chat"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    is_archived: bool = False
    is_pinned: bool = False
    tags: list["ChatTag"] = Field(default_factory=list)


class ChatTag(BaseModel):
    """Tag for organizing chats."""

    id: str = Field(default_factory=generate_uuid)
    name: str
    color: str = "#6B7280"


class Message(BaseModel):
    """Chat message model."""

    id: str = Field(default_factory=generate_uuid)
    chat_id: str
    role: Literal["user", "assistant", "system"]
    content: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    artifact_type: Optional[Literal["youtube", "pdf", "image"]] = None
    artifact_data: Optional[dict[str, Any]] = None


class TranscriptSegment(BaseModel):
    """A single segment of a video transcript."""

    text: str
    start: float  # Start time in seconds
    duration: float  # Duration in seconds

    @property
    def end(self) -> float:
        """End time in seconds."""
        return self.start + self.duration


class Transcript(BaseModel):
    """YouTube video transcript model."""

    id: str = Field(default_factory=generate_uuid)
    video_id: str
    video_url: str
    video_title: Optional[str] = None
    language_code: str = "en"
    is_generated: bool = False
    segments: list[TranscriptSegment] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    @property
    def full_text(self) -> str:
        """Get the full transcript text."""
        return " ".join(seg.text for seg in self.segments)


class Configuration(BaseModel):
    """Application configuration entry."""

    key: str
    value: dict[str, Any]
    category: Literal["llm", "mcp", "ui", "general"] = "general"


class MCPServer(BaseModel):
    """MCP server configuration."""

    id: str = Field(default_factory=generate_uuid)
    name: str
    transport_type: Literal["stdio", "sse"]
    command: Optional[str] = None  # For stdio transport
    args: Optional[list[str]] = None  # For stdio transport
    url: Optional[str] = None  # For SSE transport
    env: Optional[dict[str, str]] = None  # Environment variables
    enabled: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class LLMProvider(BaseModel):
    """LLM provider configuration."""

    id: str = Field(default_factory=generate_uuid)
    name: str  # Provider key: ollama, openai, cerebras, etc.
    base_url: str
    api_key: Optional[str] = None
    model: Optional[str] = None
    is_default: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
