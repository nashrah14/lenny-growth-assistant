"""
MessageSource SQLAlchemy Model
Maintains strict, auditable grounding references to podcast transcript chunks.
"""
import uuid
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Text, Float, Integer, DateTime, ForeignKey
from backend.app.db.base import Base, GUID

class MessageSource(Base):
    __tablename__ = "message_sources"

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    message_id: Mapped[uuid.UUID] = mapped_column(GUID, ForeignKey("messages.id", ondelete="CASCADE"), nullable=False, index=True)
    chunk_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    source_title: Mapped[str] = mapped_column(String(255), nullable=False)
    source_url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    speaker: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    source_type: Mapped[str] = mapped_column(String(64), default="podcast_transcript", nullable=False)
    relevance_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    rank: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    snippet: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    # Relationships
    message: Mapped["Message"] = relationship("Message", back_populates="sources")

    def __repr__(self) -> str:
        return f"<MessageSource(id={self.id}, message_id={self.message_id}, title='{self.source_title}', rank={self.rank})>"
