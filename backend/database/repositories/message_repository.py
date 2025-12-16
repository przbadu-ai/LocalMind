"""Repository for message operations."""

import json
from datetime import datetime
from typing import Optional

from backend.database.connection import get_db
from backend.database.models import Message


class MessageRepository:
    """Repository for managing chat messages."""

    def create(self, message: Message) -> Message:
        """Create a new message."""
        with get_db() as conn:
            conn.execute(
                """
                INSERT INTO messages (id, chat_id, role, content, created_at, artifact_type, artifact_data)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    message.id,
                    message.chat_id,
                    message.role,
                    message.content,
                    message.created_at.isoformat(),
                    message.artifact_type,
                    json.dumps(message.artifact_data) if message.artifact_data else None,
                ),
            )
            conn.commit()
        return message

    def get_by_id(self, message_id: str) -> Optional[Message]:
        """Get a message by ID."""
        with get_db() as conn:
            row = conn.execute(
                "SELECT * FROM messages WHERE id = ?",
                (message_id,),
            ).fetchone()

            if not row:
                return None

            return self._row_to_message(row)

    def get_by_chat_id(
        self,
        chat_id: str,
        limit: Optional[int] = None,
    ) -> list[Message]:
        """Get all messages for a chat."""
        with get_db() as conn:
            query = """
                SELECT * FROM messages
                WHERE chat_id = ?
                ORDER BY created_at ASC
            """
            params: list = [chat_id]

            if limit:
                query += " LIMIT ?"
                params.append(limit)

            rows = conn.execute(query, params).fetchall()
            return [self._row_to_message(row) for row in rows]

    def get_recent_by_chat_id(
        self,
        chat_id: str,
        limit: int = 10,
    ) -> list[Message]:
        """Get the most recent messages for a chat."""
        with get_db() as conn:
            rows = conn.execute(
                """
                SELECT * FROM (
                    SELECT * FROM messages
                    WHERE chat_id = ?
                    ORDER BY created_at DESC
                    LIMIT ?
                ) ORDER BY created_at ASC
                """,
                (chat_id, limit),
            ).fetchall()
            return [self._row_to_message(row) for row in rows]

    def get_messages_with_artifact(
        self,
        chat_id: str,
        artifact_type: str,
    ) -> list[Message]:
        """Get messages with a specific artifact type."""
        with get_db() as conn:
            rows = conn.execute(
                """
                SELECT * FROM messages
                WHERE chat_id = ? AND artifact_type = ?
                ORDER BY created_at ASC
                """,
                (chat_id, artifact_type),
            ).fetchall()
            return [self._row_to_message(row) for row in rows]

    def update(self, message: Message) -> Message:
        """Update a message."""
        with get_db() as conn:
            conn.execute(
                """
                UPDATE messages
                SET content = ?, artifact_type = ?, artifact_data = ?
                WHERE id = ?
                """,
                (
                    message.content,
                    message.artifact_type,
                    json.dumps(message.artifact_data) if message.artifact_data else None,
                    message.id,
                ),
            )
            conn.commit()
        return message

    def delete(self, message_id: str) -> bool:
        """Delete a message."""
        with get_db() as conn:
            cursor = conn.execute(
                "DELETE FROM messages WHERE id = ?",
                (message_id,),
            )
            conn.commit()
            return cursor.rowcount > 0

    def delete_by_chat_id(self, chat_id: str) -> int:
        """Delete all messages for a chat."""
        with get_db() as conn:
            cursor = conn.execute(
                "DELETE FROM messages WHERE chat_id = ?",
                (chat_id,),
            )
            conn.commit()
            return cursor.rowcount

    def count_by_chat_id(self, chat_id: str) -> int:
        """Count messages in a chat."""
        with get_db() as conn:
            result = conn.execute(
                "SELECT COUNT(*) FROM messages WHERE chat_id = ?",
                (chat_id,),
            ).fetchone()
            return result[0] if result else 0

    def _row_to_message(self, row) -> Message:
        """Convert a database row to a Message model."""
        artifact_data = None
        if row["artifact_data"]:
            artifact_data = json.loads(row["artifact_data"])

        return Message(
            id=row["id"],
            chat_id=row["chat_id"],
            role=row["role"],
            content=row["content"],
            created_at=datetime.fromisoformat(row["created_at"]),
            artifact_type=row["artifact_type"],
            artifact_data=artifact_data,
        )
