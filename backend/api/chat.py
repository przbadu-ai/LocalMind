"""Chat streaming API endpoint."""

import asyncio
import json
import logging
from typing import Any, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

from agents.title_agent import generate_chat_title
from database.models import Chat, Message, ToolCallData
from database.repositories.chat_repository import ChatRepository
from database.repositories.config_repository import ConfigRepository
from database.repositories.message_repository import MessageRepository
from services.llm_service import ChatMessage, LLMService, StreamChunk, ToolCall, llm_service
from services.mcp_service import mcp_service
from services.youtube_service import youtube_service
from utils.youtube_utils import find_youtube_urls

router = APIRouter()
logger = logging.getLogger(__name__)

chat_repo = ChatRepository()
message_repo = MessageRepository()
config_repo = ConfigRepository()

# Track active streams for cancellation
active_streams: dict[str, asyncio.Event] = {}


class ChatStreamRequest(BaseModel):
    """Request body for streaming chat."""

    message: str
    conversation_id: Optional[str] = None
    temperature: float = 0.7
    include_transcript: bool = True
    # Optional per-chat model override
    provider: Optional[str] = None
    model: Optional[str] = None
    # Stream ID for cancellation support
    stream_id: Optional[str] = None


class CancelStreamRequest(BaseModel):
    """Request body for cancelling a stream."""

    stream_id: str


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
    stream_id: Optional[str] = None,
):
    """Generate streaming chat response."""
    # Set up cancellation event
    cancel_event = asyncio.Event()
    if stream_id:
        active_streams[stream_id] = cancel_event

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

        # Fetch MCP tools from enabled servers
        mcp_tools: list[dict[str, Any]] = []
        tool_to_server: dict[str, str] = {}
        try:
            mcp_tools, tool_to_server = await mcp_service.get_all_tools_as_openai_format()
            if mcp_tools:
                logger.info(f"Loaded {len(mcp_tools)} MCP tools for chat")
                for tool in mcp_tools:
                    logger.debug(f"  Tool: {tool['function']['name']}")
        except Exception as e:
            logger.warning(f"Failed to load MCP tools: {e}")

        # Add tool descriptions to system prompt so LLM knows about available tools
        if mcp_tools:
            tool_descriptions = []
            for tool in mcp_tools:
                # Remove server prefix for cleaner display (e.g., "Time__get_current_time" -> "get_current_time")
                full_name = tool["function"]["name"]
                display_name = full_name.split("__")[-1] if "__" in full_name else full_name
                desc = tool["function"].get("description", "No description")
                tool_descriptions.append(f"- **{display_name}**: {desc}")

            tools_section = f"""

## Available Tools
You have access to the following tools. Use them when you need real-time or accurate information:

{chr(10).join(tool_descriptions)}

**IMPORTANT TOOL USAGE RULES**:
1. When asked about current time, dates, web searches, or other real-time information, call the appropriate tool ONCE.
2. After receiving a tool result, IMMEDIATELY use that result to formulate your response. Do NOT call the same tool again.
3. Each tool call gives you accurate, real-time data. Trust the result and respond to the user.
4. If a tool returns an error, explain the issue to the user instead of retrying."""

            # Update the system message to include tools
            context_messages[0] = ChatMessage(
                role="system",
                content=context_messages[0].content + tools_section
            )

        # Notify frontend that LLM is starting
        tool_names = [t["function"]["name"] for t in mcp_tools] if mcp_tools else []
        yield {
            "event": "message",
            "data": json.dumps({
                "type": "llm_starting",
                "model": chat_llm_service.model,
                "provider": chat.provider if chat else None,
                "tools_available": len(mcp_tools),
                "tool_names": tool_names,  # Debug: show which tools are available
            }),
        }

        # Stream LLM response with tool execution loop
        full_response = ""
        all_tool_calls: list[dict[str, Any]] = []  # Track all tool calls for this response

        try:
            # Single pass - either stream content OR execute tools (not both in a loop)
            pending_tool_calls: list[ToolCall] = []

            # Stream the LLM response
            for chunk in chat_llm_service.chat_stream(
                context_messages,
                temperature=temperature,
                tools=mcp_tools if mcp_tools else None,
            ):
                # Check for cancellation
                if cancel_event.is_set():
                    yield {
                        "event": "message",
                        "data": json.dumps({
                            "type": "cancelled",
                            "message": "Stream cancelled by user",
                        }),
                    }
                    return

                if chunk.type == "content" and chunk.content:
                    full_response += chunk.content
                    yield {
                        "event": "message",
                        "data": json.dumps({
                            "type": "content",
                            "content": chunk.content,
                        }),
                    }
                elif chunk.type == "tool_call" and chunk.tool_call:
                    pending_tool_calls.append(chunk.tool_call)
                elif chunk.type == "done":
                    break

            # Execute any tool calls that were requested
            if pending_tool_calls:
                # Check for cancellation before tool execution
                if cancel_event.is_set():
                    yield {
                        "event": "message",
                        "data": json.dumps({
                            "type": "cancelled",
                            "message": "Stream cancelled by user",
                        }),
                    }
                    return

                tool_results_for_response: list[str] = []

                for tool_call in pending_tool_calls:
                    # Check for cancellation before each tool
                    if cancel_event.is_set():
                        yield {
                            "event": "message",
                            "data": json.dumps({
                                "type": "cancelled",
                                "message": "Stream cancelled by user",
                            }),
                        }
                        return

                    # Parse the prefixed tool name
                    _, original_tool_name = mcp_service.parse_tool_name(tool_call.name)
                    server_id = tool_to_server.get(tool_call.name, "")

                    # Notify frontend about tool call
                    yield {
                        "event": "message",
                        "data": json.dumps({
                            "type": "tool_call",
                            "tool_call_id": tool_call.id,
                            "tool_name": original_tool_name,
                            "tool_args": tool_call.arguments,
                            "server_id": server_id,
                        }),
                    }

                    # Execute the tool
                    tool_result: Any = {"error": "Tool execution failed"}
                    try:
                        if server_id:
                            tool_result = await mcp_service.call_tool(
                                server_id, original_tool_name, tool_call.arguments
                            )
                        else:
                            tool_result = {"error": f"No server found for tool {tool_call.name}"}
                    except Exception as e:
                        logger.error(f"Tool execution error: {e}")
                        tool_result = {"error": str(e)}

                    # Notify frontend about tool result
                    yield {
                        "event": "message",
                        "data": json.dumps({
                            "type": "tool_result",
                            "tool_call_id": tool_call.id,
                            "tool_name": original_tool_name,
                            "result": tool_result,
                        }),
                    }

                    # Track tool call for the response
                    all_tool_calls.append({
                        "id": tool_call.id,
                        "name": original_tool_name,
                        "arguments": tool_call.arguments,
                        "result": tool_result,
                    })

                    # Collect result for building response
                    result_str = json.dumps(tool_result) if isinstance(tool_result, dict) else str(tool_result)
                    tool_results_for_response.append(f"Tool {original_tool_name} result: {result_str}")

                # Build context with tool results for final response
                context_messages.append(ChatMessage(
                    role="assistant",
                    content="",
                    tool_calls=[{
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.name,
                            "arguments": json.dumps(tc.arguments),
                        },
                    } for tc in pending_tool_calls],
                ))

                # Add all tool results to context
                for i, tool_call in enumerate(pending_tool_calls):
                    result_str = json.dumps(all_tool_calls[i]["result"]) if isinstance(all_tool_calls[i]["result"], dict) else str(all_tool_calls[i]["result"])
                    context_messages.append(ChatMessage(
                        role="tool",
                        content=result_str,
                        tool_call_id=tool_call.id,
                    ))

                # Call LLM again with tool results to generate a natural language response
                # The LLM will use the tool results to formulate a helpful answer
                logger.info("Calling LLM again with tool results to generate final response")
                for chunk in chat_llm_service.chat_stream(
                    context_messages,
                    temperature=temperature,
                    tools=None,  # Don't offer tools on the follow-up call
                ):
                    # Check for cancellation
                    if cancel_event.is_set():
                        yield {
                            "event": "message",
                            "data": json.dumps({
                                "type": "cancelled",
                                "message": "Stream cancelled by user",
                            }),
                        }
                        return

                    if chunk.type == "content" and chunk.content:
                        full_response += chunk.content
                        yield {
                            "event": "message",
                            "data": json.dumps({
                                "type": "content",
                                "content": chunk.content,
                            }),
                        }
                    elif chunk.type == "done":
                        break

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

        # Save assistant message with tool calls
        if full_response or all_tool_calls:
            # Convert tool calls to ToolCallData models
            tool_calls_data = None
            if all_tool_calls:
                tool_calls_data = [
                    ToolCallData(
                        id=tc["id"],
                        name=tc["name"],
                        arguments=tc["arguments"],
                        status="completed",
                        result=tc.get("result"),
                        error=tc.get("error"),
                    )
                    for tc in all_tool_calls
                ]

            assistant_message = Message(
                chat_id=conversation_id,
                role="assistant",
                content=full_response,
                tool_calls=tool_calls_data,
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
    finally:
        # Clean up stream tracking
        if stream_id and stream_id in active_streams:
            del active_streams[stream_id]


@router.post("/chat/stream")
async def chat_stream(request: ChatStreamRequest):
    """Stream a chat response using Server-Sent Events."""
    return EventSourceResponse(
        stream_chat_response(
            message=request.message,
            conversation_id=request.conversation_id,
            temperature=request.temperature,
            include_transcript=request.include_transcript,
            stream_id=request.stream_id,
        ),
        media_type="text/event-stream",
    )


@router.post("/chat/cancel")
async def cancel_stream(request: CancelStreamRequest):
    """Cancel an active chat stream."""
    stream_id = request.stream_id
    if stream_id in active_streams:
        active_streams[stream_id].set()
        return {"success": True, "message": "Stream cancellation requested"}
    return {"success": False, "message": "Stream not found or already completed"}
