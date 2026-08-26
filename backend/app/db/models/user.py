"""
User Model for Authentication & Authorization
"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Boolean, DateTime
from sqlalchemy.orm import relationship
from backend.app.db.base import Base, GUID

class User(Base):
    __tablename__ = "users"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    name = Column(String(255), nullable=False)
    is_active = Column(Boolean(), default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    last_login_at = Column(DateTime(timezone=True), nullable=True)

    # Relationship to user's sessions
    sessions = relationship("Session", back_populates="user", cascade="all, delete-orphan", lazy="selectin")

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email} active={self.is_active}>"
