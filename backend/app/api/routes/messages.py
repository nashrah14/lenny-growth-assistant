"""
Messages API Routes (/api/v1/sessions/{session_id}/messages)
Handles Chat interactions with user ownership verification and per-user rate limiting.

Endpoints:
  POST /messages       — batch (full response, citations, confidence)
  POST /messages/stream — SSE streaming tokens (Ollama real streaming, Gemini fallback)
"""
import uuid
import json
from typing import List, AsyncGenerator
from fastapi import APIRouter, Depends, Request, status
from fastapi.responses import StreamingResponse
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
from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.core.limiter import limiter

router = APIRouter(prefix="/sessions/{session_id}/messages", tags=["Messages"])


# ─────────────────────────────────────────────────────────────────────────────
# Batch endpoint (original)
# ─────────────────────────────────────────────────────────────────────────────

@router.post(
    "",
    response_model=ChatResponse,
    status_code=status.HTTP_200_OK,
    summary="Send a message and receive a grounded RAG, Ship30, or Artifact response"
)
@limiter.limit(lambda: f"{settings.RATE_LIMIT_CHAT_PER_MINUTE}/minute")
async def post_message(
    request: Request,
    session_id: uuid.UUID,
    payload: MessageCreateRequest,
    current_user: User = Depends(get_current_user),
    chat_service: ChatService = Depends(get_chat_service)
):
    """
    Send a user message. Rate limited to RATE_LIMIT_CHAT_PER_MINUTE requests/minute
    per authenticated user. Returns HTTP 429 with Retry-After on limit breach.
    """
    response = await chat_service.process_user_message(
        session_id=session_id,
        content=payload.content,
        user_id=current_user.id,
        provider=payload.provider,
        model=payload.model,
        explicit_intent=payload.intent
    )
    return response


# ─────────────────────────────────────────────────────────────────────────────
# Streaming SSE endpoint
# ─────────────────────────────────────────────────────────────────────────────

@router.post(
    "/stream",
    summary="Send a message and receive an SSE token stream (Ollama) or buffered stream (Gemini)"
)
@limiter.limit(lambda: f"{settings.RATE_LIMIT_CHAT_PER_MINUTE}/minute")
async def post_message_stream(
    request: Request,
    session_id: uuid.UUID,
    payload: MessageCreateRequest,
    current_user: User = Depends(get_current_user),
    chat_service: ChatService = Depends(get_chat_service)
):
    """
    Server-Sent Events (SSE) streaming endpoint.

    Protocol:
      event: token      — incremental text token from the LLM
      event: done       — final event, JSON payload contains sources, confidence, metadata
      event: error      — streaming error; client should fall back to batch endpoint

    SSE Format: text/event-stream
    Each line: "data: <payload>\\n\\n"

    When provider = 'ollama' and OLLAMA_STREAMING_ENABLED = true:
      Real NDJSON token streaming from Ollama's /api/chat stream endpoint.

    When provider = 'gemini':
      Gemini does not have per-token streaming in the current SDK; full response
      is generated then yielded as a single token event so the UI can render
      incrementally rather than waiting for HTTP response body.
    """
    provider = payload.provider or settings.LLM_PROVIDER

    async def _event_generator() -> AsyncGenerator[str, None]:
        full_content = []
        try:
            if provider == "ollama" and settings.OLLAMA_STREAMING_ENABLED:
                # ── Real Ollama token streaming ──────────────────────────────
                from backend.app.llm.router import llm_router
                from backend.app.agents.skills.rag import format_context_prompt, SYSTEM_PROMPT_QA
                from backend.app.llm.base import LLMMessage
                import re

                # Step 1: retrieval (same preprocessing as batch path)
                retrieval_query = re.sub(
                    r'\b(?:create|build|generate|make|render|write)\s+(?:an?\s+)?(?:responsive\s+)?(?:html/css|html|css|js|javascript|artifact|ui\s+component|landing\s+page|dashboard|snippet|code)\b',
                    '',
                    payload.content,
                    flags=re.IGNORECASE
                ).strip()
                final_query = retrieval_query if len(retrieval_query) >= 10 else payload.content
                retrieval_result = await chat_service.retrieval.retrieve(query=final_query)
                candidates = retrieval_result.candidates

                user_prompt = format_context_prompt(payload.content, candidates)
                history = await chat_service.session_service.get_conversation_history(session_id, window_size=4)
                messages = list(history) + [LLMMessage(role="user", content=user_prompt)]

                ollama_provider = llm_router.get_provider("ollama")

                async for token in ollama_provider.generate_stream(
                    messages=messages,
                    system_instruction=SYSTEM_PROMPT_QA,
                    temperature=0.3
                ):
                    full_content.append(token)
                    yield f"event: token\ndata: {json.dumps({'token': token})}\n\n"

                    # Check for client disconnect
                    if await request.is_disconnected():
                        logger.info("SSE client disconnected during Ollama stream", extra={"operation": "sse_disconnect"})
                        return

            else:
                # ── Gemini / fallback: batch then emit as single token event ─
                response = await chat_service.process_user_message(
                    session_id=session_id,
                    content=payload.content,
                    user_id=current_user.id,
                    provider=provider,
                    model=payload.model,
                    explicit_intent=payload.intent
                )
                full_content.append(response.content)
                yield f"event: token\ndata: {json.dumps({'token': response.content})}\n\n"

                # For Gemini, persist is already done inside process_user_message
                done_payload = {
                    "message_id": response.message_id,
                    "sources": response.sources,
                    "confidence": response.diagnostics.get("confidence") if response.diagnostics else None,
                    "model_provider": response.model_provider,
                    "model_name": response.model_name,
                    "latency_ms": response.latency_ms
                }
                yield f"event: done\ndata: {json.dumps(done_payload)}\n\n"
                return

            # ── Persist Ollama streaming result ──────────────────────────────
            aggregated = "".join(full_content)
            try:
                session = await chat_service.session_service.get_session(session_id, user_id=current_user.id)
                await chat_service.message_repo.create(
                    session_id=session_id,
                    role="user",
                    content=payload.content
                )
                asst_msg = await chat_service.message_repo.create(
                    session_id=session_id,
                    role="assistant",
                    content=aggregated,
                    model_provider="ollama",
                    model_name=settings.OLLAMA_MODEL,
                    latency_ms=0,
                    intent_type="NORMAL_QA",
                    sources=[]
                )
                await chat_service.db.commit()

                done_payload = {
                    "message_id": str(asst_msg.id),
                    "sources": [],
                    "confidence": None,
                    "model_provider": "ollama",
                    "model_name": settings.OLLAMA_MODEL,
                    "latency_ms": 0
                }
            except Exception as persist_err:
                logger.error(f"SSE stream persistence failed: {persist_err}", extra={"operation": "sse_persist_error"})
                done_payload = {"error": "persistence_failed"}

            yield f"event: done\ndata: {json.dumps(done_payload)}\n\n"

        except Exception as exc:
            logger.error(f"SSE stream error: {exc}", extra={"operation": "sse_stream_error"})
            error_payload = {"code": "STREAM_ERROR", "message": "Streaming failed. Please use the batch endpoint."}
            yield f"event: error\ndata: {json.dumps(error_payload)}\n\n"

    return StreamingResponse(
        _event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive"
        }
    )


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
