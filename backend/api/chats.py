"""Chat CRUD API endpoints."""

from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from backend.database.models import Chat, Message
from backend.database.repositories.chat_repository import ChatRepository
from backend.database.repositories.message_repository import MessageRepository

router = APIRouter()

chat_repo = ChatRepository()
message_repo = MessageRepository()


class CreateChatRequest(BaseModel):
    """Request body for creating a chat."""

    title: Optional[str] = "New Chat"


class UpdateChatRequest(BaseModel):
    """Request body for updating a chat."""

    title: Optional[str] = None
    is_archived: Optional[bool] = None


class ChatResponse(BaseModel):
    """Response model for a chat."""

    id: str
    title: str
    created_at: str
    updated_at: str
    is_archived: bool
    message_count: int


class ChatWithMessagesResponse(ChatResponse):
    """Response model for a chat with messages."""

    messages: list[dict]


class MessageResponse(BaseModel):
    """Response model for a message."""

    id: str
    chat_id: str
    role: str
    content: str
    created_at: str
    artifact_type: Optional[str] = None
    artifact_data: Optional[dict] = None


@router.get("/chats")
async def get_recent_chats(
    limit: int = Query(default=20, ge=1, le=100),
    include_archived: bool = Query(default=False),
) -> list[ChatResponse]:
    """Get recent chats."""
    chats = chat_repo.get_recent(limit=limit, include_archived=include_archived)

    return [
        ChatResponse(
            id=chat.id,
            title=chat.title,
            created_at=chat.created_at.isoformat(),
            updated_at=chat.updated_at.isoformat(),
            is_archived=chat.is_archived,
            message_count=message_repo.count_by_chat_id(chat.id),
        )
        for chat in chats
    ]


@router.get("/chats/search")
async def search_chats(
    q: str = Query(..., min_length=1),
    limit: int = Query(default=20, ge=1, le=100),
) -> list[ChatResponse]:
    """Search chats by title."""
    chats = chat_repo.search(query=q, limit=limit)

    return [
        ChatResponse(
            id=chat.id,
            title=chat.title,
            created_at=chat.created_at.isoformat(),
            updated_at=chat.updated_at.isoformat(),
            is_archived=chat.is_archived,
            message_count=message_repo.count_by_chat_id(chat.id),
        )
        for chat in chats
    ]


@router.post("/chats")
async def create_chat(request: CreateChatRequest) -> ChatResponse:
    """Create a new chat."""
    chat = Chat(title=request.title or "New Chat")
    chat = chat_repo.create(chat)

    return ChatResponse(
        id=chat.id,
        title=chat.title,
        created_at=chat.created_at.isoformat(),
        updated_at=chat.updated_at.isoformat(),
        is_archived=chat.is_archived,
        message_count=0,
    )


@router.get("/chats/{chat_id}")
async def get_chat(
    chat_id: str,
    include_messages: bool = Query(default=True),
) -> ChatWithMessagesResponse:
    """Get a chat by ID."""
    chat = chat_repo.get_by_id(chat_id)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")

    messages = []
    if include_messages:
        db_messages = message_repo.get_by_chat_id(chat_id)
        messages = [
            {
                "id": msg.id,
                "chat_id": msg.chat_id,
                "role": msg.role,
                "content": msg.content,
                "created_at": msg.created_at.isoformat(),
                "artifact_type": msg.artifact_type,
                "artifact_data": msg.artifact_data,
            }
            for msg in db_messages
        ]

    return ChatWithMessagesResponse(
        id=chat.id,
        title=chat.title,
        created_at=chat.created_at.isoformat(),
        updated_at=chat.updated_at.isoformat(),
        is_archived=chat.is_archived,
        message_count=len(messages),
        messages=messages,
    )


@router.put("/chats/{chat_id}")
async def update_chat(chat_id: str, request: UpdateChatRequest) -> ChatResponse:
    """Update a chat."""
    chat = chat_repo.get_by_id(chat_id)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")

    if request.title is not None:
        chat.title = request.title
    if request.is_archived is not None:
        chat.is_archived = request.is_archived

    chat = chat_repo.update(chat)

    return ChatResponse(
        id=chat.id,
        title=chat.title,
        created_at=chat.created_at.isoformat(),
        updated_at=chat.updated_at.isoformat(),
        is_archived=chat.is_archived,
        message_count=message_repo.count_by_chat_id(chat.id),
    )


@router.delete("/chats/{chat_id}")
async def delete_chat(chat_id: str) -> dict:
    """Delete a chat."""
    if not chat_repo.delete(chat_id):
        raise HTTPException(status_code=404, detail="Chat not found")

    return {"success": True, "message": "Chat deleted"}


@router.get("/chats/{chat_id}/messages")
async def get_chat_messages(
    chat_id: str,
    limit: Optional[int] = Query(default=None, ge=1, le=1000),
) -> list[MessageResponse]:
    """Get messages for a chat."""
    chat = chat_repo.get_by_id(chat_id)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")

    messages = message_repo.get_by_chat_id(chat_id, limit=limit)

    return [
        MessageResponse(
            id=msg.id,
            chat_id=msg.chat_id,
            role=msg.role,
            content=msg.content,
            created_at=msg.created_at.isoformat(),
            artifact_type=msg.artifact_type,
            artifact_data=msg.artifact_data,
        )
        for msg in messages
    ]


@router.post("/chats/{chat_id}/archive")
async def archive_chat(chat_id: str) -> dict:
    """Archive a chat."""
    if not chat_repo.archive(chat_id):
        raise HTTPException(status_code=404, detail="Chat not found")

    return {"success": True, "message": "Chat archived"}


@router.delete("/chats/{chat_id}/archive")
async def unarchive_chat(chat_id: str) -> dict:
    """Unarchive a chat."""
    if not chat_repo.unarchive(chat_id):
        raise HTTPException(status_code=404, detail="Chat not found")

    return {"success": True, "message": "Chat unarchived"}
