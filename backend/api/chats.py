"""
Chat management API endpoints.

This module provides REST APIs for:
- Creating and managing chat conversations
- Retrieving chat history
- Getting recent and search chats
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from models.database import get_db, Chat as ChatModel, Message as MessageModel
from services.database_service import database_service
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


# Pydantic models for API responses
class MessageResponse(BaseModel):
    """Response model for a message."""
    id: str
    role: str
    content: str
    created_at: datetime
    citations: Optional[List] = None
    tokens_used: Optional[int] = None
    confidence_score: Optional[float] = None

    class Config:
        from_attributes = True


class ChatResponse(BaseModel):
    """Response model for a chat."""
    id: str
    title: str
    description: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    last_message_at: Optional[datetime] = None
    message_count: int = 0
    is_archived: bool = False
    is_pinned: bool = False
    tags: List[str] = []
    model: Optional[str] = "llama3:instruct"

    class Config:
        from_attributes = True


class ChatWithMessagesResponse(ChatResponse):
    """Response model for a chat with its messages."""
    messages: List[MessageResponse] = []


class CreateChatRequest(BaseModel):
    """Request model for creating a chat."""
    title: Optional[str] = None
    description: Optional[str] = None
    system_prompt: Optional[str] = None
    model: Optional[str] = "llama3:instruct"
    temperature: Optional[float] = 0.7


class UpdateChatRequest(BaseModel):
    """Request model for updating a chat."""
    title: Optional[str] = None
    description: Optional[str] = None
    is_archived: Optional[bool] = None
    is_pinned: Optional[bool] = None
    tags: Optional[List[str]] = None


@router.post("/chats", response_model=ChatResponse)
async def create_chat(
    request: CreateChatRequest,
    db: Session = Depends(get_db)
):
    """
    Create a new chat conversation.

    Args:
        request: Chat creation parameters
        db: Database session

    Returns:
        Created chat object
    """
    try:
        chat = database_service.create_chat(
            db,
            title=request.title,
            description=request.description
        )

        # Set additional properties if provided
        if request.system_prompt:
            chat.system_prompt = request.system_prompt
        if request.model:
            chat.model = request.model
        if request.temperature is not None:
            chat.temperature = request.temperature

        db.commit()
        db.refresh(chat)

        return ChatResponse.model_validate(chat)
    except Exception as e:
        logger.error(f"Error creating chat: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/chats", response_model=List[ChatResponse])
async def get_recent_chats(
    limit: int = Query(20, ge=1, le=100),
    include_archived: bool = Query(False),
    db: Session = Depends(get_db)
):
    """
    Get recent chat conversations.

    Args:
        limit: Maximum number of chats to return
        include_archived: Whether to include archived chats
        db: Database session

    Returns:
        List of recent chats
    """
    try:
        chats = database_service.get_recent_chats(
            db,
            limit=limit,
            include_archived=include_archived
        )
        return [ChatResponse.model_validate(chat) for chat in chats]
    except Exception as e:
        logger.error(f"Error getting recent chats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/chats/search", response_model=List[ChatResponse])
async def search_chats(
    q: str = Query(..., min_length=1),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Search chats by title or content.

    Args:
        q: Search query
        limit: Maximum number of results
        db: Database session

    Returns:
        List of matching chats
    """
    try:
        chats = database_service.search_chats(db, query=q, limit=limit)
        return [ChatResponse.model_validate(chat) for chat in chats]
    except Exception as e:
        logger.error(f"Error searching chats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/chats/{chat_id}", response_model=ChatWithMessagesResponse)
async def get_chat(
    chat_id: str,
    include_messages: bool = Query(True),
    db: Session = Depends(get_db)
):
    """
    Get a specific chat by ID.

    Args:
        chat_id: Chat ID
        include_messages: Whether to include messages
        db: Database session

    Returns:
        Chat object with optional messages
    """
    try:
        chat = database_service.get_chat(db, chat_id)
        if not chat:
            raise HTTPException(status_code=404, detail="Chat not found")

        response = ChatWithMessagesResponse.model_validate(chat)

        if include_messages:
            messages = database_service.get_chat_messages(db, chat_id)
            response.messages = [MessageResponse.model_validate(msg) for msg in messages]

        return response
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting chat {chat_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/chats/{chat_id}", response_model=ChatResponse)
async def update_chat(
    chat_id: str,
    request: UpdateChatRequest,
    db: Session = Depends(get_db)
):
    """
    Update a chat's properties.

    Args:
        chat_id: Chat ID
        request: Update parameters
        db: Database session

    Returns:
        Updated chat object
    """
    try:
        chat = database_service.update_chat(
            db,
            chat_id,
            **request.model_dump(exclude_unset=True)
        )

        if not chat:
            raise HTTPException(status_code=404, detail="Chat not found")

        return ChatResponse.model_validate(chat)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating chat {chat_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/chats/{chat_id}")
async def delete_chat(
    chat_id: str,
    db: Session = Depends(get_db)
):
    """
    Delete a chat and all its messages.

    Args:
        chat_id: Chat ID
        db: Database session

    Returns:
        Success status
    """
    try:
        success = database_service.delete_chat(db, chat_id)
        if not success:
            raise HTTPException(status_code=404, detail="Chat not found")

        return {"status": "success", "message": f"Chat {chat_id} deleted"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting chat {chat_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/chats/{chat_id}/messages", response_model=List[MessageResponse])
async def get_chat_messages(
    chat_id: str,
    limit: Optional[int] = Query(None, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """
    Get messages for a specific chat.

    Args:
        chat_id: Chat ID
        limit: Optional limit on number of messages
        db: Database session

    Returns:
        List of messages
    """
    try:
        # Verify chat exists
        chat = database_service.get_chat(db, chat_id)
        if not chat:
            raise HTTPException(status_code=404, detail="Chat not found")

        messages = database_service.get_chat_messages(db, chat_id, limit=limit)
        return [MessageResponse.model_validate(msg) for msg in messages]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting messages for chat {chat_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chats/{chat_id}/archive")
async def archive_chat(
    chat_id: str,
    db: Session = Depends(get_db)
):
    """
    Archive a chat.

    Args:
        chat_id: Chat ID
        db: Database session

    Returns:
        Success status
    """
    try:
        chat = database_service.update_chat(db, chat_id, is_archived=True)
        if not chat:
            raise HTTPException(status_code=404, detail="Chat not found")

        return {"status": "success", "message": f"Chat {chat_id} archived"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error archiving chat {chat_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chats/{chat_id}/pin")
async def pin_chat(
    chat_id: str,
    db: Session = Depends(get_db)
):
    """
    Pin a chat to the top.

    Args:
        chat_id: Chat ID
        db: Database session

    Returns:
        Success status
    """
    try:
        chat = database_service.update_chat(db, chat_id, is_pinned=True)
        if not chat:
            raise HTTPException(status_code=404, detail="Chat not found")

        return {"status": "success", "message": f"Chat {chat_id} pinned"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error pinning chat {chat_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/chats/{chat_id}/pin")
async def unpin_chat(
    chat_id: str,
    db: Session = Depends(get_db)
):
    """
    Unpin a chat.

    Args:
        chat_id: Chat ID
        db: Database session

    Returns:
        Success status
    """
    try:
        chat = database_service.update_chat(db, chat_id, is_pinned=False)
        if not chat:
            raise HTTPException(status_code=404, detail="Chat not found")

        return {"status": "success", "message": f"Chat {chat_id} unpinned"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error unpinning chat {chat_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


__all__ = ["router"]