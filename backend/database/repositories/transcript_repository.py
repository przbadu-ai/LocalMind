"""Repository for transcript operations."""

import json
from datetime import datetime
from typing import Optional

from backend.database.connection import get_db
from backend.database.models import Transcript, TranscriptSegment


class TranscriptRepository:
    """Repository for managing YouTube transcripts."""

    def create(self, transcript: Transcript) -> Transcript:
        """Create a new transcript."""
        raw_transcript = [
            {
                "text": seg.text,
                "start": seg.start,
                "duration": seg.duration,
            }
            for seg in transcript.segments
        ]

        with get_db() as conn:
            conn.execute(
                """
                INSERT INTO transcripts (id, video_id, video_url, video_title, language_code, is_generated, raw_transcript, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    transcript.id,
                    transcript.video_id,
                    transcript.video_url,
                    transcript.video_title,
                    transcript.language_code,
                    int(transcript.is_generated),
                    json.dumps(raw_transcript),
                    transcript.created_at.isoformat(),
                ),
            )
            conn.commit()
        return transcript

    def get_by_id(self, transcript_id: str) -> Optional[Transcript]:
        """Get a transcript by ID."""
        with get_db() as conn:
            row = conn.execute(
                "SELECT * FROM transcripts WHERE id = ?",
                (transcript_id,),
            ).fetchone()

            if not row:
                return None

            return self._row_to_transcript(row)

    def get_by_video_id(self, video_id: str) -> Optional[Transcript]:
        """Get a transcript by video ID."""
        with get_db() as conn:
            row = conn.execute(
                "SELECT * FROM transcripts WHERE video_id = ?",
                (video_id,),
            ).fetchone()

            if not row:
                return None

            return self._row_to_transcript(row)

    def exists(self, video_id: str) -> bool:
        """Check if a transcript exists for a video."""
        with get_db() as conn:
            result = conn.execute(
                "SELECT 1 FROM transcripts WHERE video_id = ? LIMIT 1",
                (video_id,),
            ).fetchone()
            return result is not None

    def update(self, transcript: Transcript) -> Transcript:
        """Update a transcript."""
        raw_transcript = [
            {
                "text": seg.text,
                "start": seg.start,
                "duration": seg.duration,
            }
            for seg in transcript.segments
        ]

        with get_db() as conn:
            conn.execute(
                """
                UPDATE transcripts
                SET video_url = ?, video_title = ?, language_code = ?, is_generated = ?, raw_transcript = ?
                WHERE id = ?
                """,
                (
                    transcript.video_url,
                    transcript.video_title,
                    transcript.language_code,
                    int(transcript.is_generated),
                    json.dumps(raw_transcript),
                    transcript.id,
                ),
            )
            conn.commit()
        return transcript

    def delete(self, transcript_id: str) -> bool:
        """Delete a transcript by ID."""
        with get_db() as conn:
            cursor = conn.execute(
                "DELETE FROM transcripts WHERE id = ?",
                (transcript_id,),
            )
            conn.commit()
            return cursor.rowcount > 0

    def delete_by_video_id(self, video_id: str) -> bool:
        """Delete a transcript by video ID."""
        with get_db() as conn:
            cursor = conn.execute(
                "DELETE FROM transcripts WHERE video_id = ?",
                (video_id,),
            )
            conn.commit()
            return cursor.rowcount > 0

    def get_all(self, limit: int = 100) -> list[Transcript]:
        """Get all transcripts."""
        with get_db() as conn:
            rows = conn.execute(
                """
                SELECT * FROM transcripts
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
            return [self._row_to_transcript(row) for row in rows]

    def _row_to_transcript(self, row) -> Transcript:
        """Convert a database row to a Transcript model."""
        raw_transcript = json.loads(row["raw_transcript"]) if row["raw_transcript"] else []

        segments = [
            TranscriptSegment(
                text=seg["text"],
                start=seg["start"],
                duration=seg["duration"],
            )
            for seg in raw_transcript
        ]

        return Transcript(
            id=row["id"],
            video_id=row["video_id"],
            video_url=row["video_url"],
            video_title=row["video_title"],
            language_code=row["language_code"],
            is_generated=bool(row["is_generated"]),
            segments=segments,
            created_at=datetime.fromisoformat(row["created_at"]),
        )
