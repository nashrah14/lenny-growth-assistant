"""
Security & Cryptography Module
Implements OWASP-recommended Argon2id password hashing and signed JWT session token handling.
"""
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, VerificationError, InvalidHashError

from backend.app.core.config import settings
from backend.app.core.logging import logger

# Initialize Argon2id password hasher with secure defaults
ph = PasswordHasher(
    time_cost=3,        # Number of iterations
    memory_cost=65536,  # 64 MiB
    parallelism=4,      # 4 parallel threads
    hash_len=32,
    salt_len=16
)


def hash_password(password: str) -> str:
    """Hash password using Argon2id algorithm."""
    return ph.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify plain password against stored Argon2id hash."""
    try:
        return ph.verify(hashed_password, plain_password)
    except (VerifyMismatchError, VerificationError, InvalidHashError):
        return False
    except Exception as e:
        logger.warning(f"Unexpected error during password verification: {e}")
        return False


def create_access_token(
    user_id: str,
    email: str,
    expires_delta: Optional[timedelta] = None
) -> str:
    """Create signed JWT session token with expiration and user claims."""
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    payload: Dict[str, Any] = {
        "sub": str(user_id),
        "email": email.strip().lower(),
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp())
    }

    encoded_jwt = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    """Decode and validate a JWT session token."""
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        return payload
    except jwt.ExpiredSignatureError:
        logger.debug("Session token has expired")
        return None
    except (jwt.InvalidTokenError, Exception) as e:
        logger.debug(f"Invalid session token: {e}")
        return None
