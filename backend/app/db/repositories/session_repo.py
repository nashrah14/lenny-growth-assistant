"""
Session Repository for Multi-Turn Conversations with User Isolation
"""
import uuid
from typing import List, Optional, Dict, Any
from sqlalchemy import select, update, delete
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.db.models.session import Session
from backend.app.db.models.message import Message

class SessionRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self,
        title: str = "New Conversation",
        user_id: Optional[uuid.UUID] = None,
        user_metadata: Optional[Dict[str, Any]] = None
    ) -> Session:
        session = Session(
            title=title,
            user_id=user_id,
            user_metadata=user_metadata or {}
        )
        self.db.add(session)
        await self.db.flush()
        await self.db.refresh(session)
        return session

    async def get_by_id(
        self,
        session_id: uuid.UUID,
        user_id: Optional[uuid.UUID] = None
    ) -> Optional[Session]:
        stmt = (
            select(Session)
            .where(Session.id == session_id)
            .options(
                selectinload(Session.messages).selectinload(Message.sources),
                selectinload(Session.messages).selectinload(Message.artifacts),
                selectinload(Session.artifacts)
            )
        )
        if user_id is not None:
            stmt = stmt.where(Session.user_id == user_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def list_recent(
        self,
        limit: int = 50,
        user_id: Optional[uuid.UUID] = None
    ) -> List[Session]:
        stmt = select(Session)
        if user_id is not None:
            stmt = stmt.where(Session.user_id == user_id)
        stmt = stmt.order_by(Session.updated_at.desc()).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def update_title(
        self,
        session_id: uuid.UUID,
        title: str,
        user_id: Optional[uuid.UUID] = None
    ) -> Optional[Session]:
        session = await self.get_by_id(session_id, user_id=user_id)
        if not session:
            return None
        session.title = title
        await self.db.flush()
        await self.db.refresh(session)
        return session

    async def delete(
        self,
        session_id: uuid.UUID,
        user_id: Optional[uuid.UUID] = None
    ) -> bool:
        session = await self.get_by_id(session_id, user_id=user_id)
        if not session:
            return False
        await self.db.delete(session)
        await self.db.flush()
        return True
