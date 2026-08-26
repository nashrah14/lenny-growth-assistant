"""
Message Repository
Handles CRUD operations for conversation messages and source citations.
"""
import uuid
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from sqlalchemy.orm import selectinload
from backend.app.db.models.message import Message
from backend.app.db.models.message_source import MessageSource

class MessageRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self,
        session_id: uuid.UUID,
        role: str,
        content: str,
        model_provider: Optional[str] = None,
        model_name: Optional[str] = None,
        latency_ms: Optional[int] = None,
        intent_type: Optional[str] = "NORMAL_QA",
        sources: Optional[List[Dict[str, Any]]] = None
    ) -> Message:
        message = Message(
            id=uuid.uuid4(),
            session_id=session_id,
            role=role,
            content=content,
            model_provider=model_provider,
            model_name=model_name,
            latency_ms=latency_ms,
            intent_type=intent_type
        )
        self.db.add(message)
        await self.db.flush()

        if sources:
            for src_data in sources:
                source = MessageSource(
                    id=uuid.uuid4(),
                    message_id=message.id,
                    chunk_id=str(src_data.get("chunk_id", "")),
                    source_title=str(src_data.get("source_title", "Lenny's Podcast Transcript")),
                    source_url=src_data.get("source_url"),
                    speaker=src_data.get("speaker"),
                    source_type=src_data.get("source_type", "podcast_transcript"),
                    relevance_score=src_data.get("relevance_score"),
                    rank=src_data.get("rank", 1),
                    snippet=str(src_data.get("snippet", ""))
                )
                self.db.add(source)
            await self.db.flush()

        await self.db.refresh(message)
        # Reload with sources
        stmt = (
            select(Message)
            .where(Message.id == message.id)
            .options(
                selectinload(Message.sources),
                selectinload(Message.artifacts)
            )
        )
        res = await self.db.execute(stmt)
        return res.scalar_one()

    async def get_by_id(self, message_id: uuid.UUID) -> Optional[Message]:
        stmt = (
            select(Message)
            .where(Message.id == message_id)
            .options(
                selectinload(Message.sources),
                selectinload(Message.artifacts)
            )
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_session_id(self, session_id: uuid.UUID) -> List[Message]:
        stmt = (
            select(Message)
            .where(Message.session_id == session_id)
            .options(
                selectinload(Message.sources),
                selectinload(Message.artifacts)
            )
            .order_by(Message.created_at.asc())
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_recent_history(self, session_id: uuid.UUID, limit: int = 6) -> List[Message]:
        """Fetch the last N messages for conversation history windowing."""
        stmt = (
            select(Message)
            .where(Message.session_id == session_id)
            .order_by(desc(Message.created_at))
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        # Reverse to chronological order
        messages = list(result.scalars().all())
        messages.reverse()
        return messages
