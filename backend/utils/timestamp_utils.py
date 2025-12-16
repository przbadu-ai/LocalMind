"""Timestamp formatting utilities."""


def format_timestamp(seconds: float) -> str:
    """
    Format seconds as a timestamp string.

    Args:
        seconds: Time in seconds

    Returns:
        Formatted timestamp (MM:SS or HH:MM:SS)
    """
    total_seconds = int(seconds)
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    secs = total_seconds % 60

    if hours > 0:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    return f"{minutes}:{secs:02d}"


def parse_timestamp(timestamp: str) -> float:
    """
    Parse a timestamp string to seconds.

    Args:
        timestamp: Timestamp string (MM:SS or HH:MM:SS)

    Returns:
        Time in seconds
    """
    parts = timestamp.split(":")
    if len(parts) == 2:
        minutes, seconds = map(int, parts)
        return minutes * 60 + seconds
    elif len(parts) == 3:
        hours, minutes, seconds = map(int, parts)
        return hours * 3600 + minutes * 60 + seconds
    return 0.0
