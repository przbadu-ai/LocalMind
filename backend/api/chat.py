from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any
from models.schemas import ChatRequest, ChatResponse
from services import ChatService, VectorService
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

# Initialize services
vector_service = VectorService()
chat_service = ChatService(vector_service)


@router.post("/", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Process a chat message with RAG pipeline."""
    try:
        response = await chat_service.chat(request)
        return response
    except Exception as e:
        logger.error(f"Chat processing failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/conversations/{conversation_id}/history")
async def get_conversation_history(conversation_id: str):
    """Get the history of a specific conversation."""
    try:
        history = await chat_service.get_conversation_history(conversation_id)
        if not history:
            raise HTTPException(status_code=404, detail="Conversation not found")
        return {"conversation_id": conversation_id, "messages": history}
    except Exception as e:
        logger.error(f"Failed to get conversation history: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/conversations/{conversation_id}")
async def clear_conversation(conversation_id: str):
    """Clear a specific conversation history."""
    try:
        success = await chat_service.clear_conversation(conversation_id)
        if success:
            return {"message": "Conversation cleared successfully"}
        else:
            raise HTTPException(status_code=404, detail="Conversation not found")
    except Exception as e:
        logger.error(f"Failed to clear conversation: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/feedback")
async def submit_feedback(
    conversation_id: str,
    message_index: int,
    feedback: str,
    rating: int = None
):
    """Submit feedback for a specific message."""
    # This is a placeholder for feedback collection
    # In production, you'd want to store this in a database
    return {
        "message": "Feedback received",
        "conversation_id": conversation_id,
        "message_index": message_index,
        "feedback": feedback,
        "rating": rating
    }