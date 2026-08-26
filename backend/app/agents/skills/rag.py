"""
Grounded RAG Question-Answering Skill (Normal QA)
Synthesizes answers strictly from retrieved podcast transcript passages with source attribution.
"""
from typing import List, Dict, Any, Tuple, Optional
from pydantic import BaseModel, Field
from backend.app.rag.qdrant import RetrievalCandidate
from backend.app.llm.base import LLMMessage, LLMResponse
from backend.app.llm.router import llm_router
from backend.app.core.logging import logger

SYSTEM_PROMPT_QA = """You are "The Lenny Growth Assistant", an elite product and growth advisor designed to help product managers, founders, and growth leaders.

CRITICAL GROUNDING RULES:
1. Base your answer EXCLUSIVELY on the provided Podcast Transcript Context.
2. If the provided context DOES NOT contain sufficient factual evidence to answer the question, you MUST explicitly state:
   "I couldn't find sufficient evidence in the Lenny transcript knowledge base to answer this reliably."
   Do NOT attempt to invent facts, speculate, or draw from outside knowledge.
3. Every factual claim, framework, metric, or quote MUST be attributed to the specific podcast guest and episode mentioned in the context.
4. Use clean, professional Markdown formatting with structured headings, bullet points, and bold text for readability.
5. Provide actionable, nuanced insights reflecting the depth of Lenny's podcast discussions.
"""

def format_context_prompt(query: str, candidates: List[RetrievalCandidate]) -> str:
    """Format retrieved transcript chunks into a structured prompt context."""
    if not candidates:
        return f"User Question: {query}\n\n[No relevant transcript context found in the knowledge base.]"

    context_blocks = []
    for idx, c in enumerate(candidates, start=1):
        block = (
            f"--- Context Excerpt {idx} ---\n"
            f"Episode: {c.episode_title}\n"
            f"Speaker: {c.speaker} | Timestamp: {c.timestamp}\n"
            f"URL: {c.episode_url or 'N/A'}\n"
            f"Content:\n{c.text}\n"
        )
        context_blocks.append(block)

    joined_context = "\n".join(context_blocks)
    return (
        f"Podcast Transcript Context:\n"
        f"{joined_context}\n\n"
        f"User Question: {query}\n\n"
        f"Please provide a grounded, structured answer based ONLY on the excerpts above."
    )


class RAGSkill:
    def __init__(self):
        self.router = llm_router

    async def execute(
        self,
        query: str,
        candidates: List[RetrievalCandidate],
        history: Optional[List[LLMMessage]] = None,
        provider: Optional[str] = None,
        model: Optional[str] = None
    ) -> Tuple[str, List[Dict[str, Any]], Dict[str, Any]]:
        """
        Execute grounded RAG synthesis.
        Returns (answer_content, source_citations, metadata).
        """
        user_prompt = format_context_prompt(query, candidates)

        messages: List[LLMMessage] = []
        if history:
            # Include recent conversation turns for context
            messages.extend(history)

        messages.append(LLMMessage(role="user", content=user_prompt))

        response: LLMResponse = await self.router.generate(
            messages=messages,
            system_instruction=SYSTEM_PROMPT_QA,
            temperature=0.3,  # Lower temperature for strict grounding
            provider_name=provider,
            model=model
        )

        # Build structured source citations from retrieved candidates
        sources: List[Dict[str, Any]] = []
        seen_chunks = set()

        for idx, c in enumerate(candidates, start=1):
            if c.chunk_id not in seen_chunks:
                seen_chunks.add(c.chunk_id)
                snippet = c.text[:250] + ("..." if len(c.text) > 250 else "")
                sources.append({
                    "chunk_id": c.chunk_id,
                    "source_title": c.episode_title,
                    "source_url": c.episode_url,
                    "speaker": c.speaker,
                    "source_type": "podcast_transcript",
                    "relevance_score": c.score,
                    "rank": idx,
                    "snippet": snippet
                })

        metadata = {
            "model_provider": response.model_provider,
            "model_name": response.model_name,
            "latency_ms": response.latency_ms,
            "input_tokens": response.input_tokens,
            "output_tokens": response.output_tokens,
            "grounded": len(candidates) > 0 and "couldn't find sufficient evidence" not in response.content.lower()
        }

        return response.content, sources, metadata


# Global RAG skill singleton
rag_skill = RAGSkill()
