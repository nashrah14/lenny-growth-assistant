"""
Artifact Repository
Handles CRUD operations for generated artifacts.
"""
import uuid
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from backend.app.db.models.artifact import Artifact

class ArtifactRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self,
        session_id: uuid.UUID,
        artifact_type: str,
        title: str,
        content: str,
        raw_content: str,
        message_id: Optional[uuid.UUID] = None,
        metadata_json: Optional[Dict[str, Any]] = None
    ) -> Artifact:
        artifact = Artifact(
            id=uuid.uuid4(),
            session_id=session_id,
            message_id=message_id,
            artifact_type=artifact_type,
            title=title,
            content=content,
            raw_content=raw_content,
            metadata_json=metadata_json or {}
        )
        self.db.add(artifact)
        await self.db.flush()
        await self.db.refresh(artifact)
        return artifact

    async def get_by_id(self, artifact_id: uuid.UUID) -> Optional[Artifact]:
        stmt = select(Artifact).where(Artifact.id == artifact_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def list_by_session_id(self, session_id: uuid.UUID) -> List[Artifact]:
        stmt = (
            select(Artifact)
            .where(Artifact.session_id == session_id)
            .order_by(desc(Artifact.created_at))
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
