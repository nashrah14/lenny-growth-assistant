"""
Session SQLAlchemy Model
Represents an isolated conversation session.
"""
import uuid
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Column, String, DateTime, JSON, ForeignKey
from backend.app.db.base import Base, GUID

class Session(Base):
    __tablename__ = "sessions"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    user_id = Column(GUID(), ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)
    title = Column(String(255), nullable=False, default="New Conversation")
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    user_metadata = Column(JSON, nullable=True, default=dict)

    # Relationships
    user = relationship("User", back_populates="sessions")
    messages = relationship("Message", back_populates="session", cascade="all, delete-orphan", lazy="selectin", order_by="Message.created_at")
    artifacts = relationship("Artifact", back_populates="session", cascade="all, delete-orphan", lazy="selectin", order_by="Artifact.created_at.desc()")

    def __repr__(self) -> str:
        return f"<Session(id={self.id}, title='{self.title}')>"
