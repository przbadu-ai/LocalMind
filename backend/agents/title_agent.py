"""Title generation agent using LLM."""

from typing import Optional

from services.llm_service import ChatMessage, llm_service


def generate_chat_title(message: str, max_length: int = 50) -> str:
    """
    Generate a concise, meaningful title for a chat based on the first message.

    Args:
        message: The first message in the chat
        max_length: Maximum length of the title

    Returns:
        A concise title for the chat
    """
    # If LLM is not configured, fall back to truncating the message
    if not llm_service._ensure_client():
        return _fallback_title(message, max_length)

    try:
        system_prompt = """You are a title generator. Generate a very short, concise title (3-6 words) that captures the main topic or intent of the user's message.

Rules:
- Maximum 6 words
- No quotes or special characters
- Be specific and descriptive
- Use title case
- Don't include "Chat about" or similar prefixes
- For YouTube URLs, use "YouTube Video Analysis" or similar
- For code questions, mention the language/topic
- For general questions, capture the key subject

Examples:
- "How do I sort a list in Python?" → "Python List Sorting"
- "https://youtube.com/watch?v=..." → "YouTube Video Analysis"
- "Can you explain quantum computing?" → "Quantum Computing Explained"
- "Write a poem about the ocean" → "Ocean Poetry Request"
- "Debug this React component" → "React Component Debugging"
"""

        messages = [
            ChatMessage(role="system", content=system_prompt),
            ChatMessage(role="user", content=f"Generate a title for this message:\n\n{message[:500]}")
        ]

        # Use low temperature for consistent results
        title = llm_service.chat(messages, temperature=0.3, max_tokens=20)

        # Clean up the title
        title = title.strip().strip('"\'').strip()

        # Ensure it's not too long
        if len(title) > max_length:
            title = title[:max_length - 3] + "..."

        return title if title else _fallback_title(message, max_length)

    except Exception as e:
        # Fall back to simple truncation on any error
        return _fallback_title(message, max_length)


def _fallback_title(message: str, max_length: int = 50) -> str:
    """
    Generate a fallback title by truncating the message.

    Args:
        message: The message to truncate
        max_length: Maximum length

    Returns:
        Truncated message as title
    """
    # Remove URLs for cleaner titles
    import re
    clean_message = re.sub(r'https?://\S+', '[URL]', message)

    # Take first line and truncate
    first_line = clean_message.split('\n')[0].strip()

    if len(first_line) <= max_length:
        return first_line

    return first_line[:max_length - 3] + "..."


async def generate_chat_title_async(message: str, max_length: int = 50) -> str:
    """
    Async version of generate_chat_title.

    Args:
        message: The first message in the chat
        max_length: Maximum length of the title

    Returns:
        A concise title for the chat
    """
    # For now, just wrap the sync version
    # In the future, this could use async LLM calls
    import asyncio
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, generate_chat_title, message, max_length)
