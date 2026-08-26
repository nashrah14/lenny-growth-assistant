"""
Ingestion Repository
Handles recording of dataset ingestion jobs and run status.
"""
import uuid
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from backend.app.db.models.ingestion_run import IngestionRun

class IngestionRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def start_run(self, metadata: Optional[Dict[str, Any]] = None) -> IngestionRun:
        run = IngestionRun(
            id=uuid.uuid4(),
            started_at=datetime.now(timezone.utc),
            status="RUNNING",
            document_count=0,
            chunk_count=0,
            run_metadata=metadata or {}
        )
        self.db.add(run)
        await self.db.flush()
        await self.db.refresh(run)
        return run

    async def complete_run(
        self,
        run_id: uuid.UUID,
        document_count: int,
        chunk_count: int,
        error_summary: Optional[str] = None
    ) -> Optional[IngestionRun]:
        stmt = select(IngestionRun).where(IngestionRun.id == run_id)
        result = await self.db.execute(stmt)
        run = result.scalar_one_or_none()
        if run:
            run.completed_at = datetime.now(timezone.utc)
            run.status = "FAILED" if error_summary and document_count == 0 else "COMPLETED"
            run.document_count = document_count
            run.chunk_count = chunk_count
            run.error_summary = error_summary
            await self.db.flush()
            await self.db.refresh(run)
        return run

    async def fail_run(self, run_id: uuid.UUID, error: str) -> Optional[IngestionRun]:
        stmt = select(IngestionRun).where(IngestionRun.id == run_id)
        result = await self.db.execute(stmt)
        run = result.scalar_one_or_none()
        if run:
            run.completed_at = datetime.now(timezone.utc)
            run.status = "FAILED"
            run.error_summary = error
            await self.db.flush()
            await self.db.refresh(run)
        return run

    async def get_latest_run(self) -> Optional[IngestionRun]:
        stmt = select(IngestionRun).order_by(desc(IngestionRun.started_at)).limit(1)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
