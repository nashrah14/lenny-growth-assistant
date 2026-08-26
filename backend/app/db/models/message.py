"""
Message SQLAlchemy Model
Stores conversation turns, model provenance, and latency telemetry.
"""
import uuid
from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Text, Integer, DateTime, ForeignKey
from backend.app.db.base import Base, GUID

class Message(Base):
    __tablename__ = "messages"

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(GUID, ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    role: Mapped[str] = mapped_column(String(32), nullable=False)  # "user", "assistant", "system"
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True
    )
    model_provider: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)  # "gemini", "ollama"
    model_name: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    latency_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    intent_type: Mapped[Optional[str]] = mapped_column(String(32), nullable=True, default="NORMAL_QA")  # "NORMAL_QA", "SHIP30", "ARTIFACT"

    # Relationships
    session: Mapped["Session"] = relationship("Session", back_populates="messages")
    sources: Mapped[List["MessageSource"]] = relationship(
        "MessageSource",
        back_populates="message",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="MessageSource.rank.asc()"
    )
    artifacts: Mapped[List["Artifact"]] = relationship(
        "Artifact",
        back_populates="message",
        cascade="all, delete-orphan",
        lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<Message(id={self.id}, role='{self.role}', session_id={self.session_id})>"
