"""
Database service for managing chats and messages.

This service provides high-level operations for:
- Creating and managing chat conversations
- Storing and retrieving messages
- Managing chat history and metadata
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import desc, or_
from models.database import Chat, Message, MessageReference, Document, get_db, init_database
from models.schemas import ChatRequest, ChatResponse
import logging
import json

logger = logging.getLogger(__name__)


class DatabaseService:
    """
    Service for managing database operations.

    Provides methods for CRUD operations on chats, messages,
    and related entities.
    """

    def __init__(self):
        """Initialize the database service."""
        # Ensure database is initialized
        init_database()
        logger.info("Database service initialized")

    def create_chat(self, db: Session, title: str = None, description: str = None) -> Chat:
        """
        Create a new chat conversation.

        Args:
            db: Database session
            title: Optional chat title
            description: Optional chat description

        Returns:
            Created Chat object
        """
        if not title:
            title = f"New Chat {datetime.now().strftime('%Y-%m-%d %H:%M')}"

        chat = Chat(
            title=title,
            description=description,
            message_count=0,
            last_message_at=datetime.utcnow()
        )

        db.add(chat)
        db.commit()
        db.refresh(chat)

        logger.info(f"Created new chat: {chat.id}")
        return chat

    def get_chat(self, db: Session, chat_id: str) -> Optional[Chat]:
        """
        Get a chat by ID.

        Args:
            db: Database session
            chat_id: Chat ID

        Returns:
            Chat object or None if not found
        """
        return db.query(Chat).filter(Chat.id == chat_id).first()

    def get_recent_chats(self, db: Session, limit: int = 20, include_archived: bool = False) -> List[Chat]:
        """
        Get recent chat conversations.

        Args:
            db: Database session
            limit: Maximum number of chats to return
            include_archived: Whether to include archived chats

        Returns:
            List of Chat objects ordered by last activity
        """
        query = db.query(Chat)

        if not include_archived:
            query = query.filter(Chat.is_archived == False)

        # Order by pinned first, then by last message time
        chats = query.order_by(
            desc(Chat.is_pinned),
            desc(Chat.last_message_at)
        ).limit(limit).all()

        return chats

    def update_chat(self, db: Session, chat_id: str, **kwargs) -> Optional[Chat]:
        """
        Update a chat's properties.

        Args:
            db: Database session
            chat_id: Chat ID
            **kwargs: Properties to update

        Returns:
            Updated Chat object or None if not found
        """
        chat = self.get_chat(db, chat_id)
        if not chat:
            return None

        # Update allowed fields
        allowed_fields = ['title', 'description', 'is_archived', 'is_pinned', 'tags',
                         'model', 'temperature', 'max_tokens', 'system_prompt']

        for key, value in kwargs.items():
            if key in allowed_fields and value is not None:
                setattr(chat, key, value)

        chat.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(chat)

        return chat

    def delete_chat(self, db: Session, chat_id: str) -> bool:
        """
        Delete a chat and all its messages.

        Args:
            db: Database session
            chat_id: Chat ID

        Returns:
            True if deleted, False if not found
        """
        chat = self.get_chat(db, chat_id)
        if not chat:
            return False

        db.delete(chat)
        db.commit()

        logger.info(f"Deleted chat: {chat_id}")
        return True

    def add_message(self, db: Session, chat_id: str, role: str, content: str,
                   metadata: Dict[str, Any] = None) -> Optional[Message]:
        """
        Add a message to a chat.

        Args:
            db: Database session
            chat_id: Chat ID
            role: Message role ('user' or 'assistant')
            content: Message content
            metadata: Optional metadata (citations, context, etc.)

        Returns:
            Created Message object or None if chat not found
        """
        chat = self.get_chat(db, chat_id)
        if not chat:
            logger.error(f"Chat not found: {chat_id}")
            return None

        message = Message(
            chat_id=chat_id,
            role=role,
            content=content,
            created_at=datetime.utcnow()
        )

        # Add metadata if provided
        if metadata:
            if 'citations' in metadata:
                message.citations = metadata['citations']
            if 'context' in metadata:
                message.context_used = metadata['context']
            if 'tokens_used' in metadata:
                message.tokens_used = metadata['tokens_used']
            if 'processing_time_ms' in metadata:
                message.processing_time_ms = metadata['processing_time_ms']
            if 'confidence_score' in metadata:
                message.confidence_score = metadata['confidence_score']

        db.add(message)

        # Update chat metadata
        chat.message_count += 1
        chat.last_message_at = datetime.utcnow()
        chat.updated_at = datetime.utcnow()

        # Update chat title if it's the first user message
        if chat.message_count == 1 and role == 'user':
            # Use first 50 chars of message as title
            chat.title = content[:50] + "..." if len(content) > 50 else content

        db.commit()
        db.refresh(message)

        logger.info(f"Added {role} message to chat {chat_id}")
        return message

    def get_chat_messages(self, db: Session, chat_id: str, limit: int = None) -> List[Message]:
        """
        Get all messages for a chat.

        Args:
            db: Database session
            chat_id: Chat ID
            limit: Optional limit on number of messages

        Returns:
            List of Message objects ordered by creation time
        """
        query = db.query(Message).filter(Message.chat_id == chat_id)
        query = query.order_by(Message.created_at)

        if limit:
            query = query.limit(limit)

        return query.all()

    def search_chats(self, db: Session, query: str, limit: int = 20) -> List[Chat]:
        """
        Search chats by title or message content.

        Args:
            db: Database session
            query: Search query
            limit: Maximum number of results

        Returns:
            List of matching Chat objects
        """
        # Search in chat titles and descriptions
        chat_results = db.query(Chat).filter(
            or_(
                Chat.title.ilike(f"%{query}%"),
                Chat.description.ilike(f"%{query}%")
            )
        ).limit(limit).all()

        # Also search in messages (get unique chat IDs)
        message_chats = db.query(Message.chat_id).filter(
            Message.content.ilike(f"%{query}%")
        ).distinct().limit(limit).all()

        chat_ids = [c.chat_id for c in message_chats]
        message_chat_results = db.query(Chat).filter(Chat.id.in_(chat_ids)).all() if chat_ids else []

        # Combine and deduplicate results
        seen_ids = set()
        combined_results = []

        for chat in chat_results + message_chat_results:
            if chat.id not in seen_ids:
                seen_ids.add(chat.id)
                combined_results.append(chat)
                if len(combined_results) >= limit:
                    break

        return combined_results

    def get_or_create_chat(self, db: Session, conversation_id: str = None) -> Chat:
        """
        Get an existing chat or create a new one.

        Args:
            db: Database session
            conversation_id: Optional conversation ID

        Returns:
            Chat object
        """
        if conversation_id:
            chat = self.get_chat(db, conversation_id)
            if chat:
                return chat

        # Create new chat if not found or no ID provided
        return self.create_chat(db)

    def update_message(self, db: Session, message_id: str, content: str = None,
                      metadata: Dict[str, Any] = None) -> Optional[Message]:
        """
        Update a message.

        Args:
            db: Database session
            message_id: Message ID
            content: New content (optional)
            metadata: New metadata (optional)

        Returns:
            Updated Message object or None if not found
        """
        message = db.query(Message).filter(Message.id == message_id).first()
        if not message:
            return None

        if content is not None:
            message.content = content
            message.is_edited = True
            message.edited_at = datetime.utcnow()

        if metadata:
            if 'citations' in metadata:
                message.citations = metadata['citations']
            if 'context' in metadata:
                message.context_used = metadata['context']

        db.commit()
        db.refresh(message)

        return message

    def delete_message(self, db: Session, message_id: str) -> bool:
        """
        Delete a message.

        Args:
            db: Database session
            message_id: Message ID

        Returns:
            True if deleted, False if not found
        """
        message = db.query(Message).filter(Message.id == message_id).first()
        if not message:
            return False

        # Update chat message count
        chat = message.chat
        if chat:
            chat.message_count = max(0, chat.message_count - 1)
            chat.updated_at = datetime.utcnow()

        db.delete(message)
        db.commit()

        return True


# Create singleton instance
database_service = DatabaseService()

__all__ = ["database_service", "DatabaseService"]