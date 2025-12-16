"""YouTube URL parsing utilities."""

import re
from typing import Optional

# Patterns for matching YouTube URLs
YOUTUBE_PATTERNS = [
    # Standard watch URLs
    r"(?:https?://)?(?:www\.)?youtube\.com/watch\?v=([a-zA-Z0-9_-]{11})",
    # Short URLs
    r"(?:https?://)?(?:www\.)?youtu\.be/([a-zA-Z0-9_-]{11})",
    # Embed URLs
    r"(?:https?://)?(?:www\.)?youtube\.com/embed/([a-zA-Z0-9_-]{11})",
    # Mobile URLs
    r"(?:https?://)?m\.youtube\.com/watch\?v=([a-zA-Z0-9_-]{11})",
    # YouTube Shorts
    r"(?:https?://)?(?:www\.)?youtube\.com/shorts/([a-zA-Z0-9_-]{11})",
]

# Combined pattern for URL detection
YOUTUBE_URL_PATTERN = re.compile(
    r"(?:https?://)?(?:www\.|m\.)?(?:youtube\.com/(?:watch\?v=|embed/|shorts/)|youtu\.be/)([a-zA-Z0-9_-]{11})"
)


def extract_video_id(url: str) -> Optional[str]:
    """
    Extract the video ID from a YouTube URL.

    Args:
        url: A YouTube URL or video ID

    Returns:
        The 11-character video ID, or None if not found
    """
    # If it's already just a video ID (11 chars, alphanumeric with - and _)
    if re.match(r"^[a-zA-Z0-9_-]{11}$", url):
        return url

    # Try each pattern
    for pattern in YOUTUBE_PATTERNS:
        match = re.search(pattern, url)
        if match:
            return match.group(1)

    return None


def is_youtube_url(text: str) -> bool:
    """
    Check if a string contains a YouTube URL.

    Args:
        text: Text to check

    Returns:
        True if the text contains a YouTube URL
    """
    return bool(YOUTUBE_URL_PATTERN.search(text))


def find_youtube_urls(text: str) -> list[dict[str, str]]:
    """
    Find all YouTube URLs in a text.

    Args:
        text: Text to search

    Returns:
        List of dicts with 'url' and 'video_id' keys
    """
    results = []
    seen_ids = set()

    for match in YOUTUBE_URL_PATTERN.finditer(text):
        video_id = match.group(1)
        if video_id not in seen_ids:
            seen_ids.add(video_id)
            results.append({
                "url": match.group(0),
                "video_id": video_id,
            })

    return results


def build_youtube_url(video_id: str, timestamp: Optional[float] = None) -> str:
    """
    Build a YouTube URL from a video ID.

    Args:
        video_id: The YouTube video ID
        timestamp: Optional timestamp in seconds

    Returns:
        A YouTube watch URL
    """
    url = f"https://www.youtube.com/watch?v={video_id}"
    if timestamp is not None and timestamp > 0:
        url += f"&t={int(timestamp)}s"
    return url


def build_embed_url(video_id: str, timestamp: Optional[float] = None) -> str:
    """
    Build a YouTube embed URL from a video ID.

    Args:
        video_id: The YouTube video ID
        timestamp: Optional start timestamp in seconds

    Returns:
        A YouTube embed URL
    """
    url = f"https://www.youtube.com/embed/{video_id}?enablejsapi=1&rel=0"
    if timestamp is not None and timestamp > 0:
        url += f"&start={int(timestamp)}"
    return url
