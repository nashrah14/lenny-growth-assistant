"""
Sessions API Routes (/api/v1/sessions)
Implements Multi-Turn Session CRUD with strict authenticated User Isolation.
"""
import uuid
from typing import List
from fastapi import APIRouter, Depends, status
from backend.app.db.models.user import User
from backend.app.api.deps import (
    get_session_service,
    get_current_user,
    SessionService,
    SessionResponse,
    SessionDetailResponse,
    SessionCreateRequest,
    SessionUpdateRequest
)

router = APIRouter(prefix="/sessions", tags=["Sessions"])

@router.post(
    "",
    response_model=SessionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new conversation session"
)
async def create_session(
    payload: SessionCreateRequest,
    current_user: User = Depends(get_current_user),
    session_service: SessionService = Depends(get_session_service)
):
    session = await session_service.create_session(
        title=payload.title or "New Conversation",
        user_id=current_user.id,
        user_metadata=payload.user_metadata
    )
    return session


@router.get(
    "",
    response_model=List[SessionResponse],
    summary="List recent conversation sessions for authenticated user"
)
async def list_sessions(
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    session_service: SessionService = Depends(get_session_service)
):
    sessions = await session_service.list_sessions(limit=limit, user_id=current_user.id)
    return sessions


@router.get(
    "/{session_id}",
    response_model=SessionDetailResponse,
    summary="Retrieve session details, message history, and generated artifacts"
)
async def get_session(
    session_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    session_service: SessionService = Depends(get_session_service)
):
    session = await session_service.get_session(session_id, user_id=current_user.id)
    return session


@router.patch(
    "/{session_id}",
    response_model=SessionResponse,
    summary="Update session title"
)
async def update_session(
    session_id: uuid.UUID,
    payload: SessionUpdateRequest,
    current_user: User = Depends(get_current_user),
    session_service: SessionService = Depends(get_session_service)
):
    session = await session_service.update_session_title(
        session_id=session_id,
        title=payload.title,
        user_id=current_user.id
    )
    return session


@router.delete(
    "/{session_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a conversation session"
)
async def delete_session(
    session_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    session_service: SessionService = Depends(get_session_service)
):
    await session_service.delete_session(session_id=session_id, user_id=current_user.id)
    return None
