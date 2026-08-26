"""
User Repository for Authentication and User Queries
"""
import uuid
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.db.models.user import User

class UserRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, user_id: uuid.UUID) -> Optional[User]:
        stmt = select(User).where(User.id == user_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> Optional[User]:
        normalized_email = email.strip().lower()
        stmt = select(User).where(User.email == normalized_email)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def create(self, email: str, password_hash: str, name: str) -> User:
        normalized_email = email.strip().lower()
        user = User(
            email=normalized_email,
            password_hash=password_hash,
            name=name.strip(),
            is_active=True
        )
        self.db.add(user)
        await self.db.flush()
        await self.db.refresh(user)
        return user

    async def update_last_login(self, user_id: uuid.UUID) -> None:
        stmt = (
            update(User)
            .where(User.id == user_id)
            .values(last_login_at=datetime.now(timezone.utc))
        )
        await self.db.execute(stmt)
        await self.db.flush()
