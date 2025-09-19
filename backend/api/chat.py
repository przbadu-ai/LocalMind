"""
Chat API endpoints for RAG-based conversations.

This module handles all chat-related operations including message processing,
conversation management, and feedback collection.
"""

from fastapi import APIRouter, HTTPException, Query, Path
from fastapi.responses import StreamingResponse
from typing import Optional, Dict, Any, AsyncGenerator
from models.schemas import ChatRequest, ChatResponse
from services import ChatService, VectorService
import logging
import json

logger = logging.getLogger(__name__)
router = APIRouter()

# Initialize services
vector_service = VectorService()
chat_service = ChatService(vector_service)


@router.post("/stream")
async def chat_stream(request: ChatRequest):
    """
    Stream chat responses using Server-Sent Events (SSE).

    This endpoint streams responses in real-time from the Ollama API,
    providing a better user experience for longer responses.

    Args:
        request: ChatRequest containing the message and parameters

    Returns:
        StreamingResponse with SSE formatted data
    """
    async def generate():
        try:
            # Generate response chunks
            async for chunk in chat_service.chat_stream(request):
                # Format as SSE
                data = json.dumps(chunk)
                yield f"data: {data}\n\n"
        except Exception as e:
            logger.error(f"Streaming failed: {str(e)}")
            error_data = json.dumps({"error": str(e)})
            yield f"data: {error_data}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # Disable Nginx buffering
        }
    )


@router.post("/", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Process a chat message using RAG pipeline.

    This endpoint processes user messages by:
    1. Searching for relevant context from the vector store
    2. Building citations from matched documents
    3. Generating a response using the LLM with context
    4. Storing the conversation history

    Args:
        request: ChatRequest containing the message and parameters

    Returns:
        ChatResponse with generated text, citations, and metadata

    Raises:
        HTTPException: 500 if processing fails

    Example:
        ```python
        response = requests.post("/api/v1/chat/", json={
            "message": "What is machine learning?",
            "include_citations": True,
            "temperature": 0.7
        })
        ```
    """
    try:
        response = await chat_service.chat(request)
        return response
    except Exception as e:
        logger.error(f"Chat processing failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/conversations/{conversation_id}/history")
async def get_conversation_history(
    conversation_id: str = Path(..., description="Unique conversation identifier")
):
    """
    Retrieve the complete history of a conversation.

    Args:
        conversation_id: Unique identifier of the conversation

    Returns:
        Dict containing conversation_id and list of messages

    Raises:
        HTTPException: 404 if conversation not found
        HTTPException: 500 if retrieval fails

    Example:
        ```python
        response = requests.get("/api/v1/chat/conversations/abc123/history")
        # Returns: {"conversation_id": "abc123", "messages": [...]}
        ```
    """
    try:
        history = await chat_service.get_conversation_history(conversation_id)
        if not history:
            raise HTTPException(status_code=404, detail="Conversation not found")
        return {"conversation_id": conversation_id, "messages": history}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get conversation history: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/conversations/{conversation_id}")
async def clear_conversation(
    conversation_id: str = Path(..., description="Conversation to clear")
):
    """
    Clear/delete a specific conversation history.

    This permanently removes all messages from the conversation.
    Useful for privacy or starting fresh.

    Args:
        conversation_id: ID of conversation to clear

    Returns:
        Success message

    Raises:
        HTTPException: 404 if conversation not found
        HTTPException: 500 if deletion fails
    """
    try:
        success = await chat_service.clear_conversation(conversation_id)
        if success:
            return {"message": "Conversation cleared successfully"}
        else:
            raise HTTPException(status_code=404, detail="Conversation not found")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to clear conversation: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/feedback")
async def submit_feedback(
    conversation_id: str = Query(..., description="Conversation ID"),
    message_index: int = Query(..., ge=0, description="Message index in conversation"),
    feedback: str = Query(..., min_length=1, description="Feedback text"),
    rating: Optional[int] = Query(None, ge=1, le=5, description="Rating 1-5")
):
    """
    Submit feedback for a specific message in a conversation.

    Collects user feedback to improve response quality.
    Currently stores in memory; production should use persistent storage.

    Args:
        conversation_id: ID of the conversation
        message_index: Index of the message being rated
        feedback: Text feedback from user
        rating: Optional numeric rating (1-5)

    Returns:
        Confirmation of feedback receipt

    Note:
        This is a placeholder implementation. Production systems should:
        - Store feedback in a database
        - Implement analytics dashboards
        - Use feedback for model fine-tuning
    """
    return {
        "message": "Feedback received",
        "conversation_id": conversation_id,
        "message_index": message_index,
        "feedback": feedback,
        "rating": rating
    }