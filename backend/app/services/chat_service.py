"""
Chat Service Orchestrator
Coordinates intent routing, hybrid RAG retrieval, skill execution, and relational persistence.
"""
import uuid
import time
import re
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.services.session_service import SessionService
from backend.app.db.repositories.message_repo import MessageRepository
from backend.app.db.repositories.artifact_repo import ArtifactRepository
from backend.app.rag.retrieval import retrieval_engine, HybridRetrievalResult
from backend.app.agents.router import intent_router, IntentType
from backend.app.agents.skills.rag import rag_skill
from backend.app.agents.skills.ship30 import ship30_skill
from backend.app.agents.skills.artifact import artifact_skill
from backend.app.artifacts.generator import GeneratedArtifact
from backend.app.core.logging import logger

class ChatResponse(BaseModel):
    session_id: str
    message_id: str
    role: str = "assistant"
    content: str
    intent_type: str
    model_provider: str
    model_name: str
    latency_ms: int
    sources: List[Dict[str, Any]] = Field(default_factory=list)
    artifact: Optional[Dict[str, Any]] = None
    diagnostics: Optional[Dict[str, Any]] = None


class ChatService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.session_service = SessionService(db)
        self.message_repo = MessageRepository(db)
        self.artifact_repo = ArtifactRepository(db)
        self.retrieval = retrieval_engine

    async def process_user_message(
        self,
        session_id: uuid.UUID,
        content: str,
        user_id: Optional[uuid.UUID] = None,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        explicit_intent: Optional[str] = None
    ) -> ChatResponse:
        start_time = time.perf_counter()

        # Step 1: Ensure session exists and belongs to the authenticated user
        session = await self.session_service.get_session(session_id, user_id=user_id)

        # Step 2: Persist incoming user message
        user_msg = await self.message_repo.create(
            session_id=session_id,
            role="user",
            content=content
        )

        # Step 3: Fetch sliding window of past conversation context
        history = await self.session_service.get_conversation_history(session_id, window_size=4)

        # Step 4: Hybrid RAG Retrieval (Dense + BM25 + RRF + Cross-Encoder Reranker)
        retrieval_query = re.sub(
            r'\b(?:create|build|generate|make|render|write)\s+(?:an?\s+)?(?:responsive\s+)?(?:html/css|html|css|js|javascript|artifact|ui\s+component|landing\s+page|dashboard|snippet|code)\b',
            '',
            content,
            flags=re.IGNORECASE
        )
        retrieval_query = re.sub(r'\brender\s+it\s+as\s+(?:an?\s+)?(?:html/css\s+)?artifact\b', '', retrieval_query, flags=re.IGNORECASE).strip()
        final_search_query = retrieval_query if len(retrieval_query) >= 10 else content

        retrieval_result: HybridRetrievalResult = await self.retrieval.retrieve(query=final_search_query)
        candidates = retrieval_result.candidates

        # Step 5: Classify intent & route to designated skill
        intent = intent_router.classify(query=content, explicit_intent=explicit_intent)

        # Step 6: Execute skill
        generated_artifact_obj: Optional[GeneratedArtifact] = None
        artifact_db_record = None

        if intent == IntentType.SHIP30:
            assistant_content, sources, meta = await ship30_skill.execute(
                topic_or_query=content,
                candidates=candidates,
                history=history,
                provider=provider,
                model=model
            )
        elif intent == IntentType.ARTIFACT:
            assistant_content, generated_artifact_obj, sources, meta = await artifact_skill.execute(
                prompt=content,
                candidates=candidates,
                history=history,
                provider=provider,
                model=model
            )
        else:
            assistant_content, sources, meta = await rag_skill.execute(
                query=content,
                candidates=candidates,
                history=history,
                provider=provider,
                model=model
            )

        total_latency_ms = int((time.perf_counter() - start_time) * 1000)

        # Step 7: Persist assistant message and source citations
        asst_msg = await self.message_repo.create(
            session_id=session_id,
            role="assistant",
            content=assistant_content,
            model_provider=meta.get("model_provider"),
            model_name=meta.get("model_name"),
            latency_ms=total_latency_ms,
            intent_type=intent.value,
            sources=sources
        )

        # Step 8: Persist generated artifact if applicable
        artifact_payload = None
        if generated_artifact_obj:
            artifact_db_record = await self.artifact_repo.create(
                session_id=session_id,
                message_id=asst_msg.id,
                artifact_type=generated_artifact_obj.artifact_type,
                title=generated_artifact_obj.title,
                content=generated_artifact_obj.content,
                raw_content=generated_artifact_obj.raw_content,
                metadata_json={"skill": intent.value}
            )
            artifact_payload = {
                "id": str(artifact_db_record.id),
                "artifact_type": artifact_db_record.artifact_type,
                "title": artifact_db_record.title,
                "content": artifact_db_record.content,
                "raw_content": artifact_db_record.raw_content,
                "created_at": artifact_db_record.created_at.isoformat()
            }

        # Step 9: If first turn, generate a clean title for the session
        if session.title == "New Conversation":
            # Derive simple title from first 6 words of content
            words = content.strip().split()
            clean_title = " ".join(words[:6]).capitalize()
            if len(words) > 6:
                clean_title += "..."
            await self.session_service.update_session_title(session_id, clean_title)

        await self.db.commit()

        logger.info(
            f"Processed chat message in {total_latency_ms}ms (Intent: {intent.value}, Sources: {len(sources)})",
            extra={"operation": "chat_processed", "latency_ms": total_latency_ms, "session_id": str(session_id)}
        )

        return ChatResponse(
            session_id=str(session_id),
            message_id=str(asst_msg.id),
            role="assistant",
            content=assistant_content,
            intent_type=intent.value,
            model_provider=meta.get("model_provider", "unknown"),
            model_name=meta.get("model_name", "unknown"),
            latency_ms=total_latency_ms,
            sources=sources,
            artifact=artifact_payload,
            diagnostics=retrieval_result.diagnostics.model_dump()
        )
