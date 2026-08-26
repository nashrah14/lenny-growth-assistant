"""
IngestionRun SQLAlchemy Model
Tracks dataset ingestion jobs, document counts, chunk counts, and health.
"""
import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Text, Integer, DateTime, JSON
from backend.app.db.base import Base, GUID

class IngestionRun(Base):
    __tablename__ = "ingestion_runs"

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="RUNNING", nullable=False)  # "RUNNING", "COMPLETED", "FAILED"
    document_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    chunk_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    error_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    run_metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True, default=dict)

    def __repr__(self) -> str:
        return f"<IngestionRun(id={self.id}, status='{self.status}', docs={self.document_count}, chunks={self.chunk_count})>"
