"""
API Dependencies and Pydantic Schemas
Defines request/response contracts for FastAPI endpoints and authentication dependencies.
"""
import uuid
from typing import List, Optional, Dict, Any, Union
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict, field_validator
from fastapi import Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.config import settings
from backend.app.core.security import decode_access_token
from backend.app.core.exceptions import AppException
from backend.app.db.session import get_db
from backend.app.db.models.user import User
from backend.app.db.repositories.user_repo import UserRepository
from backend.app.services.auth_service import AuthService
from backend.app.services.session_service import SessionService
from backend.app.services.chat_service import ChatService


# ----------------- Auth Request & Response Schemas -----------------

class SignupRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, description="User full name")
    email: str = Field(..., description="User email address")
    password: str = Field(..., min_length=8, description="User password (min 8 characters)")
    confirm_password: Optional[str] = Field(default=None, description="Password confirmation")


class LoginRequest(BaseModel):
    email: str = Field(..., description="User email address")
    password: str = Field(..., description="User password")


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    email: str
    name: str
    is_active: bool
    created_at: datetime
    last_login_at: Optional[datetime] = None

    @field_validator("id", mode="before")
    @classmethod
    def serialize_id(cls, v):
        return str(v) if v is not None else None


class AuthResponse(BaseModel):
    user: UserResponse
    message: str = "Authentication successful"


class HealthResponse(BaseModel):
    status: str
    version: str
    environment: str
    timestamp: str
    database: str
    qdrant: str
    llm_providers: Dict[str, bool]


# ----------------- Chat Request Schemas -----------------

class SessionCreateRequest(BaseModel):
    title: Optional[str] = Field(default="New Conversation", description="Initial session title")
    user_metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Custom metadata")


class SessionUpdateRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=255, description="Updated session title")


class MessageCreateRequest(BaseModel):
    content: str = Field(..., min_length=1, description="User query or prompt")
    provider: Optional[str] = Field(default=None, description="LLM provider: 'gemini' or 'ollama'")
    model: Optional[str] = Field(default=None, description="Specific model name override")
    intent: Optional[str] = Field(default=None, description="Explicit intent override: 'NORMAL_QA', 'SHIP30', 'ARTIFACT'")


class ArtifactCreateRequest(BaseModel):
    session_id: Union[str, uuid.UUID]
    artifact_type: str = Field(..., description="'html' or 'markdown'")
    title: str = Field(..., min_length=1)
    content: str = Field(..., description="Raw HTML or Markdown content")
    message_id: Optional[Union[str, uuid.UUID]] = None


# ----------------- Chat Response Schemas -----------------

class SourceCitationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: Optional[Union[str, uuid.UUID]] = None
    chunk_id: str
    source_title: str
    source_url: Optional[str] = None
    speaker: Optional[str] = None
    source_type: str = "podcast_transcript"
    relevance_score: Optional[float] = None
    rank: int = 1
    snippet: str

    @field_validator("id", mode="before")
    @classmethod
    def serialize_id(cls, v):
        return str(v) if v is not None else None


class ArtifactResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    session_id: str
    message_id: Optional[str] = None
    artifact_type: str
    title: str
    content: str
    raw_content: str
    created_at: datetime
    metadata_json: Optional[Dict[str, Any]] = None

    @field_validator("id", "session_id", "message_id", mode="before")
    @classmethod
    def serialize_uuid(cls, v):
        return str(v) if v is not None else None


class MessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    session_id: str
    role: str
    content: str
    created_at: datetime
    model_provider: Optional[str] = None
    model_name: Optional[str] = None
    latency_ms: Optional[int] = None
    intent_type: Optional[str] = None
    sources: List[SourceCitationResponse] = Field(default_factory=list)
    artifacts: List[ArtifactResponse] = Field(default_factory=list)

    @field_validator("id", "session_id", mode="before")
    @classmethod
    def serialize_uuid(cls, v):
        return str(v) if v is not None else None


class SessionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    title: str
    created_at: datetime
    updated_at: datetime
    user_metadata: Optional[Dict[str, Any]] = None

    @field_validator("id", mode="before")
    @classmethod
    def serialize_id(cls, v):
        return str(v) if v is not None else None


class SessionDetailResponse(SessionResponse):
    model_config = ConfigDict(from_attributes=True)
    messages: List[MessageResponse] = Field(default_factory=list)
    artifacts: List[ArtifactResponse] = Field(default_factory=list)


# ----------------- Dependency Injectors -----------------

def get_auth_service(db: AsyncSession = Depends(get_db)) -> AuthService:
    return AuthService(db)


def get_session_service(db: AsyncSession = Depends(get_db)) -> SessionService:
    return SessionService(db)


def get_chat_service(db: AsyncSession = Depends(get_db)) -> ChatService:
    return ChatService(db)


async def get_current_user(
    request: Request,
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    Extract and validate authenticated user from HttpOnly session cookie or Authorization header.
    Raises 401 UNAUTHORIZED if missing, invalid, expired, or inactive.
    """
    token: Optional[str] = request.cookies.get(settings.COOKIE_NAME)

    if not token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header[7:].strip()

    if not token:
        raise AppException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            message="Authentication required. Please log in.",
            error_code="UNAUTHORIZED"
        )

    payload = decode_access_token(token)
    if not payload or "sub" not in payload:
        raise AppException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            message="Your session has expired. Please log in again.",
            error_code="SESSION_EXPIRED"
        )

    try:
        user_uuid = uuid.UUID(payload["sub"])
    except ValueError:
        raise AppException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            message="Invalid session payload.",
            error_code="INVALID_TOKEN"
        )

    user_repo = UserRepository(db)
    user = await user_repo.get_by_id(user_uuid)

    if not user:
        raise AppException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            message="User account no longer exists.",
            error_code="USER_NOT_FOUND"
        )

    if not user.is_active:
        raise AppException(
            status_code=status.HTTP_403_FORBIDDEN,
            message="User account has been disabled.",
            error_code="ACCOUNT_DISABLED"
        )

    return user
