"""
Integration Tests for Session Management & Persistence
"""
import pytest
import uuid
from backend.app.services.session_service import SessionService
from backend.app.core.exceptions import SessionNotFoundError

@pytest.mark.asyncio
async def test_session_crud_and_isolation(test_db_session):
    service = SessionService(test_db_session)

    # 1. Create Session A
    session_a = await service.create_session(title="Growth Strategy Chat")
    assert session_a.id is not None
    assert session_a.title == "Growth Strategy Chat"

    # 2. Create Session B
    session_b = await service.create_session(title="Pricing Breakdown Chat")
    assert session_b.id != session_a.id

    # 3. Add message to Session A
    msg_a = await service.message_repo.create(
        session_id=session_a.id,
        role="user",
        content="How do we measure CAC payback?"
    )

    # 4. Add message to Session B
    msg_b = await service.message_repo.create(
        session_id=session_b.id,
        role="user",
        content="What is tier-based pricing?"
    )

    # Verify Isolation: Session A only contains msg_a, Session B only contains msg_b
    messages_a = await service.get_messages(session_a.id)
    messages_b = await service.get_messages(session_b.id)

    assert len(messages_a) == 1
    assert messages_a[0].id == msg_a.id
    assert messages_a[0].content == "How do we measure CAC payback?"

    assert len(messages_b) == 1
    assert messages_b[0].id == msg_b.id
    assert messages_b[0].content == "What is tier-based pricing?"

    # 5. History windowing
    history_a = await service.get_conversation_history(session_a.id, window_size=5)
    assert len(history_a) == 1
    assert history_a[0].role == "user"

    # 6. Delete Session A
    await service.delete_session(session_a.id)
    with pytest.raises(SessionNotFoundError):
        await service.get_session(session_a.id)

    # Session B still exists
    session_b_check = await service.get_session(session_b.id)
    assert session_b_check is not None
