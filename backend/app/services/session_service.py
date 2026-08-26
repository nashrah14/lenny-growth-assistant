"""
Session Service
Business logic for managing conversational sessions and message history with user isolation.
"""
import uuid
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.db.repositories.session_repo import SessionRepository
from backend.app.db.repositories.message_repo import MessageRepository
from backend.app.db.models.session import Session
from backend.app.db.models.message import Message
from backend.app.core.exceptions import SessionNotFoundError
from backend.app.llm.base import LLMMessage

class SessionService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.session_repo = SessionRepository(db)
        self.message_repo = MessageRepository(db)

    async def create_session(
        self,
        title: str = "New Conversation",
        user_id: Optional[uuid.UUID] = None,
        user_metadata: Optional[Dict[str, Any]] = None
    ) -> Session:
        return await self.session_repo.create(
            title=title,
            user_id=user_id,
            user_metadata=user_metadata
        )

    async def get_session(
        self,
        session_id: uuid.UUID,
        user_id: Optional[uuid.UUID] = None
    ) -> Session:
        session = await self.session_repo.get_by_id(session_id, user_id=user_id)
        if not session:
            raise SessionNotFoundError(str(session_id))
        return session

    async def list_sessions(
        self,
        limit: int = 50,
        user_id: Optional[uuid.UUID] = None
    ) -> List[Session]:
        return await self.session_repo.list_recent(limit=limit, user_id=user_id)

    async def update_session_title(
        self,
        session_id: uuid.UUID,
        title: str,
        user_id: Optional[uuid.UUID] = None
    ) -> Session:
        session = await self.session_repo.update_title(session_id, title, user_id=user_id)
        if not session:
            raise SessionNotFoundError(str(session_id))
        return session

    async def delete_session(
        self,
        session_id: uuid.UUID,
        user_id: Optional[uuid.UUID] = None
    ) -> bool:
        success = await self.session_repo.delete(session_id, user_id=user_id)
        if not success:
            raise SessionNotFoundError(str(session_id))
        return True

    async def get_messages(
        self,
        session_id: uuid.UUID,
        user_id: Optional[uuid.UUID] = None
    ) -> List[Message]:
        # Verifies session belongs to user
        await self.get_session(session_id, user_id=user_id)
        return await self.message_repo.get_by_session_id(session_id)

    async def get_conversation_history(
        self,
        session_id: uuid.UUID,
        window_size: int = 6
    ) -> List[LLMMessage]:
        """Fetch sliding window of past messages formatted for LLM context."""
        recent_messages = await self.message_repo.get_recent_history(session_id, limit=window_size)
        llm_messages: List[LLMMessage] = []
        for msg in recent_messages:
            if msg.role in ("user", "assistant"):
                llm_messages.append(LLMMessage(role=msg.role, content=msg.content))
        return llm_messages
