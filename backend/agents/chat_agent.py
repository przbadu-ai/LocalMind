"""Chat agent using Pydantic AI."""

from dataclasses import dataclass
from typing import Optional

from pydantic import BaseModel, Field
from pydantic_ai import Agent, RunContext
from pydantic_ai.models.openai import OpenAIModel

from backend.config import settings
from backend.database.models import Transcript
from backend.utils.youtube_utils import find_youtube_urls


@dataclass
class ChatDeps:
    """Dependencies for the chat agent."""

    current_transcript: Optional[Transcript] = None
    video_id: Optional[str] = None


class ChatResponse(BaseModel):
    """Response from the chat agent."""

    message: str = Field(description="The response message")
    detected_youtube_url: Optional[str] = Field(
        default=None,
        description="YouTube URL detected in the user's message",
    )
    video_id: Optional[str] = Field(
        default=None,
        description="Extracted video ID from YouTube URL",
    )


def create_chat_agent(
    base_url: Optional[str] = None,
    api_key: Optional[str] = None,
    model_name: Optional[str] = None,
) -> Agent[ChatDeps, ChatResponse]:
    """
    Create a chat agent with the specified LLM configuration.

    Args:
        base_url: OpenAI-compatible API base URL
        api_key: API key
        model_name: Model name

    Returns:
        Configured Agent instance
    """
    # Use settings if not provided
    base_url = base_url or settings.llm_base_url
    api_key = api_key or settings.llm_api_key
    model_name = model_name or settings.llm_model

    # Create OpenAI-compatible model
    model = OpenAIModel(
        model_name,
        base_url=base_url,
        api_key=api_key,
    )

    agent = Agent(
        model=model,
        deps_type=ChatDeps,
        result_type=ChatResponse,
        system_prompt="""You are a helpful AI assistant called Local Mind.

You can help users with:
- General questions and conversations
- Analyzing YouTube videos (when transcripts are available)
- Summarizing content
- Answering questions about video content

When a user shares a YouTube URL:
1. Acknowledge the video
2. If a transcript is available, offer to summarize or answer questions about it
3. Be helpful and informative

Always be conversational, precise, and helpful.""",
    )

    @agent.tool
    def detect_youtube_url(ctx: RunContext[ChatDeps], message: str) -> dict:
        """
        Detect if the message contains a YouTube URL.

        Args:
            message: The user's message

        Returns:
            Dict with detection results
        """
        urls = find_youtube_urls(message)
        if urls:
            return {
                "found": True,
                "url": urls[0]["url"],
                "video_id": urls[0]["video_id"],
            }
        return {"found": False, "url": None, "video_id": None}

    @agent.tool
    def get_transcript_context(ctx: RunContext[ChatDeps]) -> str:
        """
        Get the transcript context for the current video.

        Returns:
            Transcript text or message if not available
        """
        if ctx.deps.current_transcript:
            # Return first 4000 chars of transcript
            return ctx.deps.current_transcript.full_text[:4000]
        return "No transcript is currently loaded."

    @agent.tool
    def search_transcript(
        ctx: RunContext[ChatDeps],
        query: str,
    ) -> list[dict]:
        """
        Search the transcript for specific content.

        Args:
            query: Search query

        Returns:
            List of matching segments with timestamps
        """
        if not ctx.deps.current_transcript:
            return []

        from backend.utils.timestamp_utils import format_timestamp

        results = []
        query_lower = query.lower()

        for segment in ctx.deps.current_transcript.segments:
            if query_lower in segment.text.lower():
                results.append({
                    "text": segment.text,
                    "timestamp": format_timestamp(segment.start),
                    "start_seconds": segment.start,
                })

        return results[:10]  # Return top 10 matches

    return agent


# Simple synchronous chat function for direct use
def chat_with_agent(
    message: str,
    transcript: Optional[Transcript] = None,
    video_id: Optional[str] = None,
    conversation_history: Optional[list[dict]] = None,
) -> ChatResponse:
    """
    Simple synchronous chat function.

    Args:
        message: User's message
        transcript: Optional current transcript
        video_id: Optional current video ID
        conversation_history: Optional list of previous messages

    Returns:
        ChatResponse object
    """
    agent = create_chat_agent()
    deps = ChatDeps(current_transcript=transcript, video_id=video_id)

    # Build the prompt with history if provided
    if conversation_history:
        history_text = "\n".join(
            f"{msg['role'].title()}: {msg['content']}"
            for msg in conversation_history[-5:]  # Last 5 messages
        )
        full_message = f"Previous conversation:\n{history_text}\n\nUser: {message}"
    else:
        full_message = message

    result = agent.run_sync(full_message, deps=deps)
    return result.data
