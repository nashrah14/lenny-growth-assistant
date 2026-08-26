"""
Artifacts API Routes (/api/v1/artifacts)
Handles saving and retrieving generated artifacts with user session verification.
"""
import uuid
from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.db.session import get_db
from backend.app.db.models.user import User
from backend.app.db.repositories.artifact_repo import ArtifactRepository
from backend.app.artifacts.sanitizer import sanitize_html, sanitize_markdown
from backend.app.core.exceptions import ArtifactNotFoundError
from backend.app.api.deps import (
    get_session_service,
    get_current_user,
    SessionService,
    ArtifactResponse,
    ArtifactCreateRequest
)

router = APIRouter(prefix="/artifacts", tags=["Artifacts"])

@router.post(
    "",
    response_model=ArtifactResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create or save an artifact"
)
async def create_artifact(
    payload: ArtifactCreateRequest,
    current_user: User = Depends(get_current_user),
    session_service: SessionService = Depends(get_session_service),
    db: AsyncSession = Depends(get_db)
):
    session_uuid = uuid.UUID(str(payload.session_id))
    # Verify session ownership
    await session_service.get_session(session_uuid, user_id=current_user.id)

    repo = ArtifactRepository(db)
    
    # Sanitize content based on type
    if payload.artifact_type.lower() == "html":
        sanitized = sanitize_html(payload.content)
    else:
        sanitized = sanitize_markdown(payload.content)

    msg_uuid = uuid.UUID(str(payload.message_id)) if payload.message_id else None

    artifact = await repo.create(
        session_id=session_uuid,
        message_id=msg_uuid,
        artifact_type=payload.artifact_type.lower(),
        title=payload.title,
        content=sanitized,
        raw_content=payload.content
    )
    await db.commit()
    return ArtifactResponse(
        id=str(artifact.id),
        session_id=str(artifact.session_id),
        message_id=str(artifact.message_id) if artifact.message_id else None,
        artifact_type=artifact.artifact_type,
        title=artifact.title,
        content=artifact.content,
        raw_content=artifact.raw_content,
        created_at=artifact.created_at,
        metadata_json=artifact.metadata_json
    )


@router.get(
    "/{artifact_id}",
    response_model=ArtifactResponse,
    summary="Retrieve an artifact by ID"
)
async def get_artifact(
    artifact_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    session_service: SessionService = Depends(get_session_service),
    db: AsyncSession = Depends(get_db)
):
    repo = ArtifactRepository(db)
    artifact = await repo.get_by_id(artifact_id)
    if not artifact:
        raise ArtifactNotFoundError(str(artifact_id))
    
    # Verify ownership via session
    await session_service.get_session(artifact.session_id, user_id=current_user.id)

    return ArtifactResponse(
        id=str(artifact.id),
        session_id=str(artifact.session_id),
        message_id=str(artifact.message_id) if artifact.message_id else None,
        artifact_type=artifact.artifact_type,
        title=artifact.title,
        content=artifact.content,
        raw_content=artifact.raw_content,
        created_at=artifact.created_at,
        metadata_json=artifact.metadata_json
    )
