"""
Artifact SQLAlchemy Model
Persists generated Markdown, HTML/CSS components, dashboards, and visual tools.
"""
import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Text, DateTime, ForeignKey, JSON
from backend.app.db.base import Base, GUID

class Artifact(Base):
    __tablename__ = "artifacts"

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(GUID, ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    message_id: Mapped[Optional[uuid.UUID]] = mapped_column(GUID, ForeignKey("messages.id", ondelete="SET NULL"), nullable=True, index=True)
    artifact_type: Mapped[str] = mapped_column(String(32), nullable=False)  # "html", "markdown"
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)  # Sanitized content for safe rendering
    raw_content: Mapped[str] = mapped_column(Text, nullable=False)  # Original model output
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    metadata_json: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True, default=dict)

    # Relationships
    session: Mapped["Session"] = relationship("Session", back_populates="artifacts")
    message: Mapped[Optional["Message"]] = relationship("Message", back_populates="artifacts")

    def __repr__(self) -> str:
        return f"<Artifact(id={self.id}, type='{self.artifact_type}', title='{self.title}')>"
