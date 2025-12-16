"""YouTube transcript API endpoints."""

from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from services.youtube_service import (
    TranscriptResult,
    get_transcript_error_help,
    youtube_service,
)
from utils.youtube_utils import extract_video_id

router = APIRouter()


# Segment grouping configuration
MIN_SEGMENT_DURATION = 10  # Minimum 10 seconds per grouped segment
MAX_SEGMENT_DURATION = 60  # Maximum 60 seconds per grouped segment
TARGET_SEGMENT_DURATION = 30  # Target around 30 seconds


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


def group_transcript_segments(segments: list, min_duration: float = MIN_SEGMENT_DURATION, max_duration: float = MAX_SEGMENT_DURATION) -> list:
    """
    Group short transcript segments into longer, more readable chunks.

    Args:
        segments: List of transcript segments with text, start, and duration
        min_duration: Minimum duration for a grouped segment (default 10s)
        max_duration: Maximum duration for a grouped segment (default 60s)

    Returns:
        List of grouped segments
    """
    if not segments:
        return []

    grouped = []
    current_group = {
        "text": "",
        "start": 0,
        "duration": 0,
    }

    for i, seg in enumerate(segments):
        seg_text = seg.get("text", "") if isinstance(seg, dict) else seg.text
        seg_start = seg.get("start", 0) if isinstance(seg, dict) else seg.start
        seg_duration = seg.get("duration", 0) if isinstance(seg, dict) else seg.duration

        # If this is the first segment in a group
        if not current_group["text"]:
            current_group = {
                "text": seg_text,
                "start": seg_start,
                "duration": seg_duration,
            }
        else:
            # Calculate the total duration if we add this segment
            potential_end = seg_start + seg_duration
            potential_duration = potential_end - current_group["start"]

            # Check if adding this segment would exceed max duration
            if potential_duration > max_duration:
                # Save current group and start a new one
                grouped.append(current_group)
                current_group = {
                    "text": seg_text,
                    "start": seg_start,
                    "duration": seg_duration,
                }
            else:
                # Add to current group
                current_group["text"] = current_group["text"] + " " + seg_text
                current_group["duration"] = potential_duration

    # Don't forget the last group
    if current_group["text"]:
        grouped.append(current_group)

    # Post-process: merge any very short trailing segments
    final_grouped = []
    for group in grouped:
        if final_grouped and group["duration"] < min_duration / 2:
            # Merge with previous if this one is very short
            prev = final_grouped[-1]
            prev["text"] = prev["text"] + " " + group["text"]
            prev["duration"] = (group["start"] + group["duration"]) - prev["start"]
        else:
            final_grouped.append(group)

    return final_grouped


def build_transcript_response(result, group_segments: bool = True) -> dict:
    """Build the transcript response dict from a TranscriptResult."""
    if not result.transcript:
        return None

    raw_segments = [
        {
            "text": seg.text,
            "start": seg.start,
            "duration": seg.duration,
        }
        for seg in result.transcript.segments
    ]

    # Group segments for better readability in the UI
    if group_segments:
        segments = group_transcript_segments(raw_segments)
    else:
        segments = raw_segments

    return {
        "id": result.transcript.id,
        "video_id": result.transcript.video_id,
        "video_url": result.transcript.video_url,
        "video_title": result.transcript.video_title,
        "language_code": result.transcript.language_code,
        "is_generated": result.transcript.is_generated,
        "segments": segments,
        "full_text": result.transcript.full_text,
        "raw_segment_count": len(raw_segments),
        "grouped_segment_count": len(segments),
    }


@router.post("/youtube/transcript")
async def extract_transcript(
    request: TranscriptRequest,
    group: bool = Query(default=True, description="Group segments into longer chunks"),
) -> TranscriptResponse:
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
            transcript=build_transcript_response(result, group_segments=group),
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
    group: bool = Query(default=True, description="Group segments into longer chunks"),
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
            transcript=build_transcript_response(result, group_segments=group),
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
