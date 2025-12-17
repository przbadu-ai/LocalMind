"""YouTube transcript extraction service."""

from typing import Optional

from pydantic import BaseModel
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import (
    NoTranscriptFound,
    TranscriptsDisabled,
    VideoUnavailable,
)

from database.models import Transcript, TranscriptSegment
from database.repositories.transcript_repository import TranscriptRepository
from utils.youtube_utils import build_youtube_url, extract_video_id


class TranscriptResult(BaseModel):
    """Result of a transcript extraction attempt."""

    success: bool
    video_id: str
    transcript: Optional[Transcript] = None
    error_type: Optional[str] = None
    error_message: Optional[str] = None


class YouTubeService:
    """Service for extracting and managing YouTube transcripts."""

    def __init__(self):
        self.transcript_repo = TranscriptRepository()
        self.api = YouTubeTranscriptApi()

    def get_transcript(
        self,
        video_id_or_url: str,
        languages: list[str] = ["en", "hi", "es", "fr", "de", "pt", "ja", "ko", "zh"],
        use_cache: bool = True,
    ) -> TranscriptResult:
        """
        Get the transcript for a YouTube video.

        Args:
            video_id_or_url: YouTube video ID or URL
            languages: Preferred languages in order
            use_cache: Whether to use cached transcripts

        Returns:
            TranscriptResult with success status and transcript or error info
        """
        video_id = extract_video_id(video_id_or_url)
        if not video_id:
            return TranscriptResult(
                success=False,
                video_id=video_id_or_url,
                error_type="InvalidURL",
                error_message="Could not extract a valid YouTube video ID from the provided URL.",
            )

        # Check cache first
        if use_cache:
            cached = self.transcript_repo.get_by_video_id(video_id)
            if cached:
                return TranscriptResult(
                    success=True,
                    video_id=video_id,
                    transcript=cached,
                )

        # Fetch from YouTube using the new API
        try:
            # First, list available transcripts to find the best one
            transcript_list = self.api.list(video_id)

            # Try to find a transcript in preferred languages
            transcript_data = None
            is_generated = False
            language_code = "en"

            # First try manually created transcripts
            try:
                transcript = transcript_list.find_manually_created_transcript(languages)
                transcript_data = transcript.fetch()
                is_generated = False
                language_code = transcript.language_code
            except NoTranscriptFound:
                # Fall back to auto-generated
                try:
                    transcript = transcript_list.find_generated_transcript(languages)
                    transcript_data = transcript.fetch()
                    is_generated = True
                    language_code = transcript.language_code
                except NoTranscriptFound:
                    # Try any available transcript
                    available = list(transcript_list)
                    if available:
                        transcript = available[0]
                        transcript_data = transcript.fetch()
                        is_generated = transcript.is_generated
                        language_code = transcript.language_code

            if not transcript_data:
                return TranscriptResult(
                    success=False,
                    video_id=video_id,
                    error_type="NoTranscriptFound",
                    error_message="No transcript found for this video in any language.",
                )

            # Convert to our model - handle both dict and FetchedTranscriptSnippet
            segments = []
            for seg in transcript_data:
                # The new API returns objects with attributes, not dicts
                if hasattr(seg, 'text'):
                    segments.append(TranscriptSegment(
                        text=seg.text,
                        start=seg.start,
                        duration=seg.duration,
                    ))
                else:
                    # Fallback for dict format
                    segments.append(TranscriptSegment(
                        text=seg["text"],
                        start=seg["start"],
                        duration=seg["duration"],
                    ))

            transcript_obj = Transcript(
                video_id=video_id,
                video_url=build_youtube_url(video_id),
                language_code=language_code,
                is_generated=is_generated,
                segments=segments,
            )

            # Cache the transcript
            try:
                self.transcript_repo.create(transcript_obj)
            except Exception:
                # Ignore cache errors, we still have the transcript
                pass

            return TranscriptResult(
                success=True,
                video_id=video_id,
                transcript=transcript_obj,
            )

        except TranscriptsDisabled:
            return TranscriptResult(
                success=False,
                video_id=video_id,
                error_type="TranscriptsDisabled",
                error_message="Transcripts are disabled for this video by the owner.",
            )
        except VideoUnavailable:
            return TranscriptResult(
                success=False,
                video_id=video_id,
                error_type="VideoUnavailable",
                error_message="This video is unavailable, private, or has been removed.",
            )
        except Exception as e:
            error_type = type(e).__name__
            return TranscriptResult(
                success=False,
                video_id=video_id,
                error_type=error_type,
                error_message=str(e),
            )

    def get_available_languages(self, video_id_or_url: str) -> dict:
        """
        Get available transcript languages for a video.

        Args:
            video_id_or_url: YouTube video ID or URL

        Returns:
            Dict with 'manual' and 'generated' language lists
        """
        video_id = extract_video_id(video_id_or_url)
        if not video_id:
            return {"error": "Invalid video ID", "manual": [], "generated": []}

        try:
            transcript_list = self.api.list(video_id)

            manual = []
            generated = []

            for transcript in transcript_list:
                lang_info = {
                    "code": transcript.language_code,
                    "name": transcript.language,
                }
                if transcript.is_generated:
                    generated.append(lang_info)
                else:
                    manual.append(lang_info)

            return {"manual": manual, "generated": generated}

        except Exception as e:
            return {"error": str(e), "manual": [], "generated": []}

    def get_cached_transcript(self, video_id: str) -> Optional[Transcript]:
        """Get a cached transcript if it exists."""
        return self.transcript_repo.get_by_video_id(video_id)

    def clear_cache(self, video_id: str) -> bool:
        """Clear the cached transcript for a video."""
        return self.transcript_repo.delete_by_video_id(video_id)


def get_transcript_error_help(error_type: str) -> str:
    """
    Get user-friendly help text for transcript errors.

    Args:
        error_type: The error type from TranscriptResult

    Returns:
        Helpful message for the user
    """
    error_help = {
        "TranscriptsDisabled": """
**Transcripts are disabled for this video.**

The video owner has disabled transcripts/captions for this video.

**What you can try:**
1. Check if the video has community-contributed captions
2. Use YouTube's auto-generated captions directly on YouTube
3. Try a different video that has captions enabled
""",
        "VideoUnavailable": """
**This video is unavailable.**

The video may be private, age-restricted, or has been removed.

**What you can try:**
1. Verify the URL is correct
2. Check if you can access the video directly on YouTube
3. Make sure the video is publicly available
""",
        "NoTranscriptFound": """
**No transcript available for this video.**

This video doesn't have transcripts in any supported language.

**What you can try:**
1. Check if the video has auto-generated captions on YouTube
2. Use YouTube's "Show transcript" feature (click ... below the video)
3. Try a different video with captions
""",
        "InvalidURL": """
**Invalid YouTube URL.**

The URL provided doesn't appear to be a valid YouTube video URL.

**Supported formats:**
- youtube.com/watch?v=VIDEO_ID
- youtu.be/VIDEO_ID
- youtube.com/embed/VIDEO_ID
""",
    }

    return error_help.get(
        error_type,
        f"""
**Unable to extract transcript.**

An error occurred while trying to get the transcript: {error_type}

**What you can try:**
1. Check your internet connection
2. Try again in a few moments
3. Use YouTube's built-in transcript feature
""",
    )


# Global YouTube service instance
youtube_service = YouTubeService()
