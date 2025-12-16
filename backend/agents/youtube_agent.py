"""YouTube-specific agents for summarization and Q&A."""

from dataclasses import dataclass
from typing import Optional

from pydantic import BaseModel, Field
from pydantic_ai import Agent, RunContext
from pydantic_ai.models.openai import OpenAIModel

from backend.config import settings
from backend.database.models import Transcript
from backend.utils.timestamp_utils import format_timestamp


@dataclass
class YouTubeDeps:
    """Dependencies for YouTube agents."""

    transcript: Transcript
    video_id: str


class TimestampReference(BaseModel):
    """A reference to a specific timestamp in the video."""

    timestamp: str = Field(description="Formatted timestamp (MM:SS or HH:MM:SS)")
    start_seconds: float = Field(description="Start time in seconds")
    description: str = Field(description="Brief description of what happens at this timestamp")


class VideoSummary(BaseModel):
    """Summary of a YouTube video."""

    title: Optional[str] = Field(default=None, description="Video title if known")
    overview: str = Field(description="Brief overview of the video content (2-3 sentences)")
    key_points: list[str] = Field(description="List of main points or topics covered")
    timestamps: list[TimestampReference] = Field(
        default_factory=list,
        description="Key timestamps in the video",
    )
    duration_formatted: Optional[str] = Field(
        default=None,
        description="Total video duration",
    )


class VideoQAResponse(BaseModel):
    """Response to a question about video content."""

    answer: str = Field(description="Answer to the user's question")
    relevant_timestamps: list[TimestampReference] = Field(
        default_factory=list,
        description="Timestamps relevant to the answer",
    )
    confidence: str = Field(
        default="high",
        description="Confidence level: high, medium, or low",
    )
    source_quotes: list[str] = Field(
        default_factory=list,
        description="Relevant quotes from the transcript",
    )


def create_summary_agent(
    base_url: Optional[str] = None,
    api_key: Optional[str] = None,
    model_name: Optional[str] = None,
) -> Agent[YouTubeDeps, VideoSummary]:
    """
    Create an agent for summarizing YouTube videos.

    Args:
        base_url: OpenAI-compatible API base URL
        api_key: API key
        model_name: Model name

    Returns:
        Configured Agent instance for summarization
    """
    base_url = base_url or settings.llm_base_url
    api_key = api_key or settings.llm_api_key
    model_name = model_name or settings.llm_model

    model = OpenAIModel(
        model_name,
        base_url=base_url,
        api_key=api_key,
    )

    agent = Agent(
        model=model,
        deps_type=YouTubeDeps,
        result_type=VideoSummary,
        system_prompt="""You are an expert at analyzing and summarizing YouTube video content.

Given a video transcript, provide:
1. A clear, concise overview (2-3 sentences)
2. The main key points or topics covered (3-7 points)
3. Important timestamps that viewers should note

Be specific and reference actual content from the transcript.
Format timestamps as MM:SS or HH:MM:SS.""",
    )

    @agent.tool
    def get_full_transcript(ctx: RunContext[YouTubeDeps]) -> str:
        """Get the full transcript text."""
        transcript = ctx.deps.transcript
        # Limit to prevent token overflow
        full_text = transcript.full_text
        if len(full_text) > 8000:
            return full_text[:8000] + "... [truncated]"
        return full_text

    @agent.tool
    def get_transcript_with_timestamps(ctx: RunContext[YouTubeDeps]) -> str:
        """Get the transcript with timestamps for each segment."""
        transcript = ctx.deps.transcript
        lines = []
        for segment in transcript.segments[:100]:  # Limit segments
            timestamp = format_timestamp(segment.start)
            lines.append(f"[{timestamp}] {segment.text}")
        return "\n".join(lines)

    @agent.tool
    def get_video_duration(ctx: RunContext[YouTubeDeps]) -> str:
        """Get the total video duration."""
        transcript = ctx.deps.transcript
        if transcript.segments:
            last_segment = transcript.segments[-1]
            total_seconds = last_segment.start + last_segment.duration
            return format_timestamp(total_seconds)
        return "Unknown"

    return agent


def create_qa_agent(
    base_url: Optional[str] = None,
    api_key: Optional[str] = None,
    model_name: Optional[str] = None,
) -> Agent[YouTubeDeps, VideoQAResponse]:
    """
    Create an agent for answering questions about YouTube videos.

    Args:
        base_url: OpenAI-compatible API base URL
        api_key: API key
        model_name: Model name

    Returns:
        Configured Agent instance for Q&A
    """
    base_url = base_url or settings.llm_base_url
    api_key = api_key or settings.llm_api_key
    model_name = model_name or settings.llm_model

    model = OpenAIModel(
        model_name,
        base_url=base_url,
        api_key=api_key,
    )

    agent = Agent(
        model=model,
        deps_type=YouTubeDeps,
        result_type=VideoQAResponse,
        system_prompt="""You are an expert at analyzing YouTube video content and answering questions about it.

When answering questions:
1. Base your answers only on the transcript content
2. Cite specific timestamps when referencing parts of the video
3. Include relevant quotes from the transcript
4. Be honest about your confidence level - say "low" if the transcript doesn't clearly address the question

Format timestamps as MM:SS or HH:MM:SS.""",
    )

    @agent.tool
    def search_transcript(ctx: RunContext[YouTubeDeps], query: str) -> list[dict]:
        """
        Search the transcript for content matching a query.

        Args:
            query: Search terms

        Returns:
            List of matching segments with timestamps
        """
        transcript = ctx.deps.transcript
        results = []
        query_lower = query.lower()

        for segment in transcript.segments:
            if query_lower in segment.text.lower():
                results.append({
                    "text": segment.text,
                    "timestamp": format_timestamp(segment.start),
                    "start_seconds": segment.start,
                })

        return results[:15]  # Return top 15 matches

    @agent.tool
    def get_context_around_timestamp(
        ctx: RunContext[YouTubeDeps],
        target_seconds: float,
        context_seconds: float = 30,
    ) -> str:
        """
        Get transcript content around a specific timestamp.

        Args:
            target_seconds: Target time in seconds
            context_seconds: How many seconds of context to include (before and after)

        Returns:
            Transcript text around the timestamp
        """
        transcript = ctx.deps.transcript
        start_time = max(0, target_seconds - context_seconds)
        end_time = target_seconds + context_seconds

        segments_in_range = [
            f"[{format_timestamp(seg.start)}] {seg.text}"
            for seg in transcript.segments
            if start_time <= seg.start <= end_time
        ]

        return "\n".join(segments_in_range)

    @agent.tool
    def get_transcript_section(
        ctx: RunContext[YouTubeDeps],
        start_seconds: float,
        end_seconds: float,
    ) -> str:
        """
        Get a specific section of the transcript.

        Args:
            start_seconds: Start time in seconds
            end_seconds: End time in seconds

        Returns:
            Transcript text for the specified section
        """
        transcript = ctx.deps.transcript
        segments_in_range = [
            f"[{format_timestamp(seg.start)}] {seg.text}"
            for seg in transcript.segments
            if start_seconds <= seg.start <= end_seconds
        ]

        return "\n".join(segments_in_range)

    return agent


# Convenience functions for direct use
def summarize_video(transcript: Transcript, video_id: str) -> VideoSummary:
    """
    Summarize a video using the summary agent.

    Args:
        transcript: Video transcript
        video_id: YouTube video ID

    Returns:
        VideoSummary object
    """
    agent = create_summary_agent()
    deps = YouTubeDeps(transcript=transcript, video_id=video_id)
    result = agent.run_sync("Please summarize this video.", deps=deps)
    return result.data


def answer_video_question(
    question: str,
    transcript: Transcript,
    video_id: str,
) -> VideoQAResponse:
    """
    Answer a question about a video.

    Args:
        question: User's question
        transcript: Video transcript
        video_id: YouTube video ID

    Returns:
        VideoQAResponse object
    """
    agent = create_qa_agent()
    deps = YouTubeDeps(transcript=transcript, video_id=video_id)
    result = agent.run_sync(question, deps=deps)
    return result.data
