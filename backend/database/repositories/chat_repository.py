"""Repository for chat operations."""

import json
from datetime import datetime
from typing import Optional

from database.connection import get_db
from database.models import Chat, ChatTag


class ChatRepository:
    """Repository for managing chat conversations."""

    def create(self, chat: Chat) -> Chat:
        """Create a new chat."""
        with get_db() as conn:
            conn.execute(
                """
                INSERT INTO chats (id, title, created_at, updated_at, is_archived)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    chat.id,
                    chat.title,
                    chat.created_at.isoformat(),
                    chat.updated_at.isoformat(),
                    int(chat.is_archived),
                ),
            )
            conn.commit()
        return chat

    def get_by_id(self, chat_id: str) -> Optional[Chat]:
        """Get a chat by ID."""
        with get_db() as conn:
            row = conn.execute(
                "SELECT * FROM chats WHERE id = ?",
                (chat_id,),
            ).fetchone()

            if not row:
                return None

            return self._row_to_chat(row)

    def get_recent(
        self,
        limit: int = 20,
        include_archived: bool = False,
    ) -> list[Chat]:
        """Get recent chats."""
        with get_db() as conn:
            query = "SELECT * FROM chats"
            params: list = []

            if not include_archived:
                query += " WHERE is_archived = 0"

            query += " ORDER BY updated_at DESC LIMIT ?"
            params.append(limit)

            rows = conn.execute(query, params).fetchall()
            return [self._row_to_chat(row) for row in rows]

    def search(self, query: str, limit: int = 20) -> list[Chat]:
        """Search chats by title."""
        with get_db() as conn:
            rows = conn.execute(
                """
                SELECT * FROM chats
                WHERE title LIKE ?
                ORDER BY updated_at DESC
                LIMIT ?
                """,
                (f"%{query}%", limit),
            ).fetchall()
            return [self._row_to_chat(row) for row in rows]

    def update(self, chat: Chat) -> Chat:
        """Update a chat."""
        chat.updated_at = datetime.utcnow()
        with get_db() as conn:
            conn.execute(
                """
                UPDATE chats
                SET title = ?, updated_at = ?, is_archived = ?
                WHERE id = ?
                """,
                (
                    chat.title,
                    chat.updated_at.isoformat(),
                    int(chat.is_archived),
                    chat.id,
                ),
            )
            conn.commit()
        return chat

    def update_title(self, chat_id: str, title: str) -> bool:
        """Update chat title."""
        with get_db() as conn:
            cursor = conn.execute(
                """
                UPDATE chats
                SET title = ?, updated_at = ?
                WHERE id = ?
                """,
                (title, datetime.utcnow().isoformat(), chat_id),
            )
            conn.commit()
            return cursor.rowcount > 0

    def delete(self, chat_id: str) -> bool:
        """Delete a chat and all its messages."""
        with get_db() as conn:
            cursor = conn.execute(
                "DELETE FROM chats WHERE id = ?",
                (chat_id,),
            )
            conn.commit()
            return cursor.rowcount > 0

    def archive(self, chat_id: str) -> bool:
        """Archive a chat."""
        with get_db() as conn:
            cursor = conn.execute(
                """
                UPDATE chats
                SET is_archived = 1, updated_at = ?
                WHERE id = ?
                """,
                (datetime.utcnow().isoformat(), chat_id),
            )
            conn.commit()
            return cursor.rowcount > 0

    def unarchive(self, chat_id: str) -> bool:
        """Unarchive a chat."""
        with get_db() as conn:
            cursor = conn.execute(
                """
                UPDATE chats
                SET is_archived = 0, updated_at = ?
                WHERE id = ?
                """,
                (datetime.utcnow().isoformat(), chat_id),
            )
            conn.commit()
            return cursor.rowcount > 0

    def touch(self, chat_id: str) -> bool:
        """Update the updated_at timestamp."""
        with get_db() as conn:
            cursor = conn.execute(
                """
                UPDATE chats
                SET updated_at = ?
                WHERE id = ?
                """,
                (datetime.utcnow().isoformat(), chat_id),
            )
            conn.commit()
            return cursor.rowcount > 0

    def _row_to_chat(self, row) -> Chat:
        """Convert a database row to a Chat model."""
        return Chat(
            id=row["id"],
            title=row["title"],
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
            is_archived=bool(row["is_archived"]),
        )
