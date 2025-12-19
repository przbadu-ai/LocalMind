"""Chat streaming API endpoint."""

import asyncio
import json
import logging
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

from agents.title_agent import generate_chat_title
from database.models import Chat, Message
from database.repositories.chat_repository import ChatRepository
from database.repositories.config_repository import ConfigRepository
from database.repositories.message_repository import MessageRepository
from services.llm_service import ChatMessage, LLMService, llm_service
from services.youtube_service import youtube_service
from utils.youtube_utils import find_youtube_urls

router = APIRouter()
logger = logging.getLogger(__name__)

chat_repo = ChatRepository()
message_repo = MessageRepository()
config_repo = ConfigRepository()


class ChatStreamRequest(BaseModel):
    """Request body for streaming chat."""

    message: str
    conversation_id: Optional[str] = None
    temperature: float = 0.7
    include_transcript: bool = True
    # Optional per-chat model override
    provider: Optional[str] = None
    model: Optional[str] = None


def get_llm_service_for_chat(chat: Optional[Chat]) -> LLMService:
    """Get the appropriate LLM service for a chat.

    If the chat has a custom model/provider set, create a new service with those settings.
    Otherwise, return the global llm_service.
    """
    if chat and chat.provider and chat.model:
        # Get provider credentials
        provider = config_repo.get_llm_provider_for_use(chat.provider)
        if provider:
            return LLMService(
                base_url=provider.base_url,
                api_key=provider.api_key,
                model=chat.model,
            )
    # Fall back to global service
    return llm_service


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
        is_first_message = False

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

            # Notify frontend that we're loading transcript
            if include_transcript:
                yield {
                    "event": "message",
                    "data": json.dumps({
                        "type": "transcript_loading",
                        "video_id": video_id,
                    }),
                }

                # Fetch transcript - this must complete before LLM starts
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
                # Create new chat with a temporary title
                chat = Chat(id=conversation_id, title="New Chat")
                chat = chat_repo.create(chat)
                is_first_message = True
        else:
            chat = Chat(title="New Chat")
            chat = chat_repo.create(chat)
            conversation_id = chat.id
            is_first_message = True

        # Save user message
        user_message = Message(
            chat_id=conversation_id,
            role="user",
            content=message,
            artifact_type=artifact_type,
            artifact_data=artifact_data,
        )
        message_repo.create(user_message)

        # Check if this is really the first message
        if not is_first_message:
            is_first_message = message_repo.count_by_chat_id(conversation_id) == 1

        # Build context messages
        context_messages = []

        # System message with context
        system_content = """You are Local Mind, a helpful AI assistant.

You are a general-purpose conversational AI that can:
- Have natural conversations on any topic
- Answer questions and provide information
- Help with tasks, explanations, and problem-solving
- Analyze YouTube video content when users share video URLs

For normal conversations:
- Respond naturally and helpfully
- Match the tone of the conversation (casual greetings get casual responses)
- Keep responses concise and focused

For YouTube URLs (only when user shares a video link):
- Provide a well-structured SUMMARY with key points, NOT the raw transcript
- Use sections like: **Overview**, **Key Points**, **Main Topics**, **Takeaways**
- Reference specific timestamps when relevant (format: [MM:SS])
- Extract insights, don't just repeat what was said

IMPORTANT: Be friendly and conversational. Use markdown formatting for readability."""

        if transcript:
            # Include transcript in context - the transcript is now available
            transcript_text = transcript.full_text
            if len(transcript_text) > 8000:
                transcript_text = transcript_text[:8000] + "... [transcript truncated]"
            system_content += f"""

The user is viewing a YouTube video (ID: {video_id}).

TRANSCRIPT (for your reference only - DO NOT output this verbatim):
---
{transcript_text}
---

Based on this transcript, provide a helpful, structured response. If this is the first message about this video, give a comprehensive summary with key points and main topics discussed."""
        elif youtube_urls and not transcript:
            system_content += f"\n\nThe user shared a YouTube video (ID: {video_id}) but the transcript could not be extracted. Let them know you can't access the video content."

        context_messages.append(ChatMessage(role="system", content=system_content))

        # Add recent conversation history (only from current chat, not other chats)
        recent_messages = message_repo.get_recent_by_chat_id(conversation_id, limit=10)
        for msg in recent_messages:
            if msg.id != user_message.id:  # Don't duplicate the current message
                context_messages.append(ChatMessage(role=msg.role, content=msg.content))

        # Add current message
        context_messages.append(ChatMessage(role="user", content=message))

        # Get the appropriate LLM service for this chat (may be per-chat model)
        chat_llm_service = get_llm_service_for_chat(chat)

        # Notify frontend that LLM is starting
        yield {
            "event": "message",
            "data": json.dumps({
                "type": "llm_starting",
                "model": chat_llm_service.model,
                "provider": chat.provider if chat else None,
            }),
        }

        # Stream LLM response
        full_response = ""
        try:
            for chunk in chat_llm_service.chat_stream(context_messages, temperature=temperature):
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
                        "error": f"Cannot connect to LLM service. Please check that the LLM server is running at {chat_llm_service.base_url}",
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

        # Generate title using LLM if this is the first message
        generated_title = None
        if is_first_message:
            try:
                # Run title generation in a thread pool to not block
                loop = asyncio.get_event_loop()
                generated_title = await loop.run_in_executor(
                    None, generate_chat_title, message, 50
                )
                if generated_title:
                    chat_repo.update_title(conversation_id, generated_title)
            except Exception as e:
                logger.warning(f"Failed to generate title: {e}")
                # Fall back to truncated message
                generated_title = message[:50] + ("..." if len(message) > 50 else "")
                chat_repo.update_title(conversation_id, generated_title)

        # Send done event with title if generated
        done_data = {
            "type": "done",
            "conversation_id": conversation_id,
        }
        if generated_title:
            done_data["title"] = generated_title

        yield {
            "event": "message",
            "data": json.dumps(done_data),
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
