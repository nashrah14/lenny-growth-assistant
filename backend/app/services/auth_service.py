"""
Authentication Service
Handles user registration, credential verification, and session token generation.
"""
import uuid
import re
from typing import Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.db.models.user import User
from backend.app.db.repositories.user_repo import UserRepository
from backend.app.core.security import hash_password, verify_password, create_access_token
from backend.app.core.exceptions import AppException

class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.user_repo = UserRepository(db)

    @staticmethod
    def validate_email(email: str) -> str:
        """Validate and normalize email address."""
        if not email or not isinstance(email, str):
            raise AppException(status_code=422, message="Email address is required.", error_code="INVALID_EMAIL")
        email = email.strip().lower()
        email_regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
        if not re.match(email_regex, email):
            raise AppException(status_code=422, message="Please provide a valid email address.", error_code="INVALID_EMAIL")
        return email

    @staticmethod
    def validate_password(password: str, confirm_password: Optional[str] = None) -> None:
        """Validate password length, complexity, and confirmation match."""
        if not password or len(password) < 8:
            raise AppException(
                status_code=422,
                message="Password must be at least 8 characters long.",
                error_code="WEAK_PASSWORD"
            )
        if confirm_password is not None and password != confirm_password:
            raise AppException(
                status_code=422,
                message="Password confirmation does not match.",
                error_code="PASSWORD_MISMATCH"
            )

    async def signup(
        self,
        name: str,
        email: str,
        password: str,
        confirm_password: Optional[str] = None
    ) -> Tuple[User, str]:
        """Register a new user, hash password with Argon2id, and issue session token."""
        if not name or not name.strip():
            raise AppException(status_code=422, message="Full name is required.", error_code="INVALID_NAME")

        normalized_email = self.validate_email(email)
        self.validate_password(password, confirm_password)

        existing_user = await self.user_repo.get_by_email(normalized_email)
        if existing_user:
            raise AppException(
                status_code=409,
                message="An account with this email already exists.",
                error_code="USER_ALREADY_EXISTS"
            )

        password_hash = hash_password(password)
        user = await self.user_repo.create(
            email=normalized_email,
            password_hash=password_hash,
            name=name.strip()
        )
        await self.db.commit()

        token = create_access_token(user_id=str(user.id), email=user.email)
        return user, token

    async def login(self, email: str, password: str) -> Tuple[User, str]:
        """Authenticate user credentials and issue session token."""
        normalized_email = self.validate_email(email)
        user = await self.user_repo.get_by_email(normalized_email)

        if not user or not verify_password(password, user.password_hash):
            raise AppException(
                status_code=401,
                message="Invalid email or password.",
                error_code="INVALID_CREDENTIALS"
            )

        if not user.is_active:
            raise AppException(
                status_code=403,
                message="This user account has been disabled.",
                error_code="ACCOUNT_DISABLED"
            )

        await self.user_repo.update_last_login(user.id)
        await self.db.commit()

        token = create_access_token(user_id=str(user.id), email=user.email)
        return user, token
