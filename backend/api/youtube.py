"""YouTube transcript API endpoints."""

from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from backend.services.youtube_service import (
    TranscriptResult,
    get_transcript_error_help,
    youtube_service,
)
from backend.utils.youtube_utils import extract_video_id

router = APIRouter()


class TranscriptRequest(BaseModel):
    """Request body for extracting a transcript."""

    url: str
    languages: Optional[list[str]] = None
    use_cache: bool = True


class TranscriptSegmentResponse(BaseModel):
    """Response model for a transcript segment."""

    text: str
    start: float
    duration: float


class TranscriptResponse(BaseModel):
    """Response model for a transcript."""

    success: bool
    video_id: str
    transcript: Optional[dict] = None
    error_type: Optional[str] = None
    error_message: Optional[str] = None
    error_help: Optional[str] = None


@router.post("/youtube/transcript")
async def extract_transcript(request: TranscriptRequest) -> TranscriptResponse:
    """Extract transcript from a YouTube video."""
    languages = request.languages or ["en", "hi", "es", "fr", "de", "pt", "ja", "ko", "zh"]

    result = youtube_service.get_transcript(
        video_id_or_url=request.url,
        languages=languages,
        use_cache=request.use_cache,
    )

    if result.success and result.transcript:
        return TranscriptResponse(
            success=True,
            video_id=result.video_id,
            transcript={
                "id": result.transcript.id,
                "video_id": result.transcript.video_id,
                "video_url": result.transcript.video_url,
                "video_title": result.transcript.video_title,
                "language_code": result.transcript.language_code,
                "is_generated": result.transcript.is_generated,
                "segments": [
                    {
                        "text": seg.text,
                        "start": seg.start,
                        "duration": seg.duration,
                    }
                    for seg in result.transcript.segments
                ],
                "full_text": result.transcript.full_text,
            },
        )
    else:
        return TranscriptResponse(
            success=False,
            video_id=result.video_id,
            error_type=result.error_type,
            error_message=result.error_message,
            error_help=get_transcript_error_help(result.error_type or "Unknown"),
        )


@router.get("/youtube/transcript/{video_id}")
async def get_transcript(
    video_id: str,
    use_cache: bool = Query(default=True),
) -> TranscriptResponse:
    """Get transcript for a video by ID."""
    result = youtube_service.get_transcript(
        video_id_or_url=video_id,
        use_cache=use_cache,
    )

    if result.success and result.transcript:
        return TranscriptResponse(
            success=True,
            video_id=result.video_id,
            transcript={
                "id": result.transcript.id,
                "video_id": result.transcript.video_id,
                "video_url": result.transcript.video_url,
                "video_title": result.transcript.video_title,
                "language_code": result.transcript.language_code,
                "is_generated": result.transcript.is_generated,
                "segments": [
                    {
                        "text": seg.text,
                        "start": seg.start,
                        "duration": seg.duration,
                    }
                    for seg in result.transcript.segments
                ],
                "full_text": result.transcript.full_text,
            },
        )
    else:
        return TranscriptResponse(
            success=False,
            video_id=result.video_id,
            error_type=result.error_type,
            error_message=result.error_message,
            error_help=get_transcript_error_help(result.error_type or "Unknown"),
        )


@router.delete("/youtube/transcript/{video_id}")
async def clear_transcript_cache(video_id: str) -> dict:
    """Clear cached transcript for a video."""
    # Validate video ID
    extracted_id = extract_video_id(video_id)
    if not extracted_id:
        raise HTTPException(status_code=400, detail="Invalid video ID")

    if youtube_service.clear_cache(extracted_id):
        return {"success": True, "message": f"Cache cleared for video {extracted_id}"}
    else:
        return {"success": False, "message": "No cached transcript found"}


@router.get("/youtube/languages/{video_id}")
async def get_available_languages(video_id: str) -> dict:
    """Get available transcript languages for a video."""
    # Validate video ID
    extracted_id = extract_video_id(video_id)
    if not extracted_id:
        raise HTTPException(status_code=400, detail="Invalid video ID")

    return youtube_service.get_available_languages(extracted_id)


@router.get("/youtube/validate")
async def validate_video_id(url: str = Query(..., description="YouTube URL or video ID")) -> dict:
    """Validate and extract video ID from a URL."""
    video_id = extract_video_id(url)

    if video_id:
        return {
            "valid": True,
            "video_id": video_id,
            "url": f"https://www.youtube.com/watch?v={video_id}",
        }
    else:
        return {
            "valid": False,
            "video_id": None,
            "error": "Could not extract a valid video ID from the provided URL",
        }
