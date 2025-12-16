"""Chat streaming API endpoint."""

import json
import logging
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

from database.models import Chat, Message
from database.repositories.chat_repository import ChatRepository
from database.repositories.message_repository import MessageRepository
from services.llm_service import ChatMessage, llm_service
from services.youtube_service import youtube_service
from utils.youtube_utils import find_youtube_urls

router = APIRouter()
logger = logging.getLogger(__name__)

chat_repo = ChatRepository()
message_repo = MessageRepository()


class ChatStreamRequest(BaseModel):
    """Request body for streaming chat."""

    message: str
    conversation_id: Optional[str] = None
    temperature: float = 0.7
    include_transcript: bool = True


async def stream_chat_response(
    message: str,
    conversation_id: Optional[str],
    temperature: float,
    include_transcript: bool,
):
    """Generate streaming chat response."""
    try:
        # Check for YouTube URLs in the message
        youtube_urls = find_youtube_urls(message)
        video_id = None
        transcript = None
        artifact_type = None
        artifact_data = None

        if youtube_urls:
            video_info = youtube_urls[0]
            video_id = video_info["video_id"]
            artifact_type = "youtube"
            artifact_data = {"video_id": video_id, "url": video_info["url"]}

            # Notify frontend about YouTube detection
            yield {
                "event": "message",
                "data": json.dumps({
                    "type": "youtube_detected",
                    "video_id": video_id,
                    "url": video_info["url"],
                }),
            }

            # Try to fetch transcript
            if include_transcript:
                result = youtube_service.get_transcript(video_id)
                if result.success:
                    transcript = result.transcript
                    artifact_data["transcript_available"] = True
                    yield {
                        "event": "message",
                        "data": json.dumps({
                            "type": "transcript_status",
                            "success": True,
                            "video_id": video_id,
                            "language": transcript.language_code if transcript else None,
                            "segment_count": len(transcript.segments) if transcript else 0,
                        }),
                    }
                else:
                    artifact_data["transcript_available"] = False
                    artifact_data["transcript_error"] = result.error_message
                    yield {
                        "event": "message",
                        "data": json.dumps({
                            "type": "transcript_status",
                            "success": False,
                            "video_id": video_id,
                            "error_type": result.error_type,
                            "error_message": result.error_message,
                        }),
                    }

        # Create or get chat
        if conversation_id:
            chat = chat_repo.get_by_id(conversation_id)
            if not chat:
                # Create new chat with the provided ID
                chat = Chat(id=conversation_id, title=message[:50])
                chat = chat_repo.create(chat)
        else:
            chat = Chat(title=message[:50])
            chat = chat_repo.create(chat)
            conversation_id = chat.id

        # Save user message
        user_message = Message(
            chat_id=conversation_id,
            role="user",
            content=message,
            artifact_type=artifact_type,
            artifact_data=artifact_data,
        )
        message_repo.create(user_message)

        # Update chat title if this is the first message
        if message_repo.count_by_chat_id(conversation_id) == 1:
            title = message[:50] + ("..." if len(message) > 50 else "")
            chat_repo.update_title(conversation_id, title)

        # Build context messages
        context_messages = []

        # System message with context
        system_content = """You are a helpful AI assistant called Local Mind. You help users with various tasks including analyzing YouTube videos.

When the user shares a YouTube video:
- If a transcript is available, you can summarize it, answer questions about it, or discuss specific parts
- Reference timestamps when discussing specific parts of the video
- Be helpful and informative about the video content"""

        if transcript:
            # Include transcript in context
            transcript_text = transcript.full_text
            if len(transcript_text) > 6000:
                transcript_text = transcript_text[:6000] + "... [transcript truncated]"
            system_content += f"\n\nThe user is viewing a YouTube video (ID: {video_id}). Here is the transcript:\n\n{transcript_text}"
        elif youtube_urls and not transcript:
            system_content += f"\n\nThe user shared a YouTube video but the transcript could not be extracted. You can still discuss the video but won't have access to its content."

        context_messages.append(ChatMessage(role="system", content=system_content))

        # Add recent conversation history
        recent_messages = message_repo.get_recent_by_chat_id(conversation_id, limit=10)
        for msg in recent_messages:
            if msg.id != user_message.id:  # Don't duplicate the current message
                context_messages.append(ChatMessage(role=msg.role, content=msg.content))

        # Add current message
        context_messages.append(ChatMessage(role="user", content=message))

        # Stream LLM response
        full_response = ""
        try:
            for chunk in llm_service.chat_stream(context_messages, temperature=temperature):
                full_response += chunk
                yield {
                    "event": "message",
                    "data": json.dumps({
                        "type": "content",
                        "content": chunk,
                    }),
                }
        except Exception as e:
            logger.error(f"LLM streaming error: {e}")
            error_msg = str(e)
            if "connection" in error_msg.lower() or "refused" in error_msg.lower():
                yield {
                    "event": "message",
                    "data": json.dumps({
                        "type": "error",
                        "error": f"Cannot connect to LLM service. Please check that the LLM server is running at {llm_service.base_url}",
                    }),
                }
            else:
                yield {
                    "event": "message",
                    "data": json.dumps({
                        "type": "error",
                        "error": f"LLM error: {error_msg}",
                    }),
                }
            return

        # Save assistant message
        if full_response:
            assistant_message = Message(
                chat_id=conversation_id,
                role="assistant",
                content=full_response,
            )
            message_repo.create(assistant_message)

            # Update chat timestamp
            chat_repo.touch(conversation_id)

        # Send done event
        yield {
            "event": "message",
            "data": json.dumps({
                "type": "done",
                "conversation_id": conversation_id,
            }),
        }

    except Exception as e:
        logger.exception(f"Chat stream error: {e}")
        yield {
            "event": "message",
            "data": json.dumps({
                "type": "error",
                "error": str(e),
            }),
        }


@router.post("/chat/stream")
async def chat_stream(request: ChatStreamRequest):
    """Stream a chat response using Server-Sent Events."""
    return EventSourceResponse(
        stream_chat_response(
            message=request.message,
            conversation_id=request.conversation_id,
            temperature=request.temperature,
            include_transcript=request.include_transcript,
        ),
        media_type="text/event-stream",
    )
