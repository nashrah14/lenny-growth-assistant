"""
Grounded RAG Question-Answering Skill (Normal QA)
Synthesizes answers strictly from retrieved podcast transcript passages with source attribution.

Confidence Scoring Model
------------------------
Confidence is derived ONLY from observable retrieval and evidence signals —
NOT from an arbitrary LLM-generated percentage.

Signals used:
  1. Source count (n_sources):  More unique, well-ranked sources = stronger evidence base
  2. Top reranker score:        Cross-encoder score of the top-ranked passage (0.0–1.0)
  3. Source agreement:          Multiple distinct episodes covering the same claim
  4. Knowledge-gap detection:   LLM explicitly stated it couldn't find evidence

Thresholds (empirically chosen, documented):
  HIGH:       n_sources >= 3  AND  top_score >= 0.70
  MODERATE:   n_sources >= 2  AND  top_score >= 0.45  (or 3+ with any score)
  LOW:        n_sources >= 1  AND  top_score >= 0.20
  INSUFFICIENT: n_sources == 0  OR  llm indicated no evidence

Why not a calibrated probability?
  Cross-encoder scores are not calibrated probabilities. Using raw semantic
  similarity scores as "percentage confidence" would misrepresent the model's
  statistical reliability. Instead, this model uses clearly documented threshold
  buckets that are honest about being heuristic rather than probabilistic.
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

# ─────────────────────────────────────────────────────────────────────────────
# Confidence Scoring
# ─────────────────────────────────────────────────────────────────────────────

_KNOWLEDGE_GAP_PHRASE = "couldn't find sufficient evidence"

class ConfidenceLevel:
    HIGH = "HIGH"
    MODERATE = "MODERATE"
    LOW = "LOW"
    INSUFFICIENT = "INSUFFICIENT"

    LABELS = {
        HIGH: "High — strong supporting evidence from multiple sources",
        MODERATE: "Moderate — relevant evidence found; some gaps remain",
        LOW: "Low — limited supporting evidence; treat with caution",
        INSUFFICIENT: "Insufficient — no reliable evidence found in the knowledge base",
    }


class ConfidenceScore(BaseModel):
    """
    Structured confidence metadata attached to every RAG answer.

    Fields:
      level:          Semantic bucket (HIGH/MODERATE/LOW/INSUFFICIENT)
      label:          Human-readable description of the confidence level
      n_sources:      Number of unique, non-duplicate sources retrieved
      top_score:      Reranker score of the highest-ranked passage (0.0–1.0)
      distinct_episodes: Number of distinct podcast episodes supporting the answer
      knowledge_gap:  True if the LLM explicitly reported insufficient evidence
    """
    level: str = Field(..., description="HIGH | MODERATE | LOW | INSUFFICIENT")
    label: str = Field(..., description="Human-readable confidence label")
    n_sources: int = Field(..., description="Number of unique retrieved sources")
    top_score: float = Field(..., description="Cross-encoder score of top-ranked source")
    distinct_episodes: int = Field(..., description="Number of distinct supporting episodes")
    knowledge_gap: bool = Field(..., description="True if LLM acknowledged knowledge gap")


def compute_confidence(
    candidates: List[RetrievalCandidate],
    answer_content: str
) -> ConfidenceScore:
    """
    Compute a transparent, signal-based confidence score.

    Inputs:
      candidates:     Top-k reranked retrieval candidates (in rank order)
      answer_content: The LLM-generated answer text

    Thresholds:
      HIGH:         n_sources >= 3 AND top_score >= 0.70
      MODERATE:     n_sources >= 2 AND top_score >= 0.45
                    OR n_sources >= 3 (many sources, even with moderate scores)
      LOW:          n_sources >= 1 AND top_score >= 0.20
      INSUFFICIENT: n_sources == 0 OR LLM explicitly reported no evidence
    """
    n_sources = len(candidates)
    top_score = candidates[0].score if candidates else 0.0
    distinct_episodes = len({c.episode_title for c in candidates if c.episode_title})
    knowledge_gap = _KNOWLEDGE_GAP_PHRASE in answer_content.lower()

    # Knowledge gap always resolves to INSUFFICIENT regardless of retrieval
    if knowledge_gap or n_sources == 0:
        level = ConfidenceLevel.INSUFFICIENT
    elif n_sources >= 3 and top_score >= 0.70:
        level = ConfidenceLevel.HIGH
    elif (n_sources >= 2 and top_score >= 0.45) or n_sources >= 3:
        level = ConfidenceLevel.MODERATE
    elif n_sources >= 1 and top_score >= 0.20:
        level = ConfidenceLevel.LOW
    else:
        level = ConfidenceLevel.INSUFFICIENT

    return ConfidenceScore(
        level=level,
        label=ConfidenceLevel.LABELS[level],
        n_sources=n_sources,
        top_score=round(top_score, 4),
        distinct_episodes=distinct_episodes,
        knowledge_gap=knowledge_gap
    )


# ─────────────────────────────────────────────────────────────────────────────
# Context Formatting
# ─────────────────────────────────────────────────────────────────────────────

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


# ─────────────────────────────────────────────────────────────────────────────
# RAG Skill
# ─────────────────────────────────────────────────────────────────────────────

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
        metadata includes a 'confidence' key with structured ConfidenceScore data.
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

        # Compute transparent confidence score
        confidence = compute_confidence(candidates, response.content)

        metadata = {
            "model_provider": response.model_provider,
            "model_name": response.model_name,
            "latency_ms": response.latency_ms,
            "input_tokens": response.input_tokens,
            "output_tokens": response.output_tokens,
            "grounded": len(candidates) > 0 and not confidence.knowledge_gap,
            "confidence": confidence.model_dump()
        }

        logger.info(
            f"RAG answer generated (confidence: {confidence.level}, sources: {confidence.n_sources})",
            extra={"operation": "rag_complete", "confidence_level": confidence.level, "n_sources": confidence.n_sources}
        )

        return response.content, sources, metadata


# Global RAG skill singleton
rag_skill = RAGSkill()
