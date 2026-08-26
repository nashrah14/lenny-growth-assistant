"""
Messages API Routes (/api/v1/sessions/{session_id}/messages)
Handles Chat interactions with user ownership verification.
"""
import uuid
from typing import List
from fastapi import APIRouter, Depends, status
from backend.app.db.models.user import User
from backend.app.api.deps import (
    get_chat_service,
    get_session_service,
    get_current_user,
    ChatService,
    SessionService,
    MessageCreateRequest,
    MessageResponse
)
from backend.app.services.chat_service import ChatResponse

router = APIRouter(prefix="/sessions/{session_id}/messages", tags=["Messages"])

@router.post(
    "",
    response_model=ChatResponse,
    status_code=status.HTTP_200_OK,
    summary="Send a message and receive a grounded RAG, Ship30, or Artifact response"
)
async def post_message(
    session_id: uuid.UUID,
    payload: MessageCreateRequest,
    current_user: User = Depends(get_current_user),
    chat_service: ChatService = Depends(get_chat_service)
):
    response = await chat_service.process_user_message(
        session_id=session_id,
        content=payload.content,
        user_id=current_user.id,
        provider=payload.provider,
        model=payload.model,
        explicit_intent=payload.intent
    )
    return response


@router.get(
    "",
    response_model=List[MessageResponse],
    summary="Get all messages in a session"
)
async def get_messages(
    session_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    session_service: SessionService = Depends(get_session_service)
):
    messages = await session_service.get_messages(session_id, user_id=current_user.id)
    return messages
