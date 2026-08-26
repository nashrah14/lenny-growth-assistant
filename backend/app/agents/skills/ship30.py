"""
Ship 30 for 30 Content Generation Skill
Transforms grounded transcript insights into a high-impact, skimmable, ~1,250-word atomic essay.
"""
from typing import List, Dict, Any, Tuple, Optional
from backend.app.rag.qdrant import RetrievalCandidate
from backend.app.llm.base import LLMMessage, LLMResponse
from backend.app.llm.router import llm_router
from backend.app.agents.skills.rag import format_context_prompt
from backend.app.core.logging import logger

SHIP30_SYSTEM_PROMPT = """You are an elite growth essayist trained in the "Ship 30 for 30" writing methodology.
Your task is to transform podcast insights into an authoritative, publication-ready growth essay of approximately 1,250 words.

SHIP 30 FOR 30 WRITING PRINCIPLES:
1. THE HOOK: Open with a punchy, single-sentence provocative truth or contrarian observation. Never open with fluff like "In today's fast-paced world".
2. THE PROBLEM (AGITATION): Clearly articulate the status quo mistake 90% of product and growth teams make.
3. THE PARADIGM SHIFT: Introduce the core breakthrough framework derived from the podcast guest.
4. 3 TO 5 CORE PILLARS (SUBHEADINGS):
   - Break the framework into 3–5 distinct, named pillars.
   - Use crisp `###` subheadings.
   - Employ high-skimmability formatting: 1–2 sentence paragraphs, bullet points, and **selective bold emphasis** on critical insights.
5. TACTICAL PLAYBOOK / IMPLEMENTATION: Give the reader step-by-step instructions on what to do on Monday morning.
6. THE ULTIMATE TAKEAWAY: Conclude with a memorable summary sentence that sticks with the reader.
7. GROUNDING & ATTRIBUTION: Attribute all frameworks, quotes, and metrics explicitly to the podcast guest and episode.

Ensure the final essay is deeply detailed, reaching approximately 1,250 words of high-signal substance without generic filler.
"""

class Ship30Skill:
    def __init__(self):
        self.router = llm_router

    async def execute(
        self,
        topic_or_query: str,
        candidates: List[RetrievalCandidate],
        history: Optional[List[LLMMessage]] = None,
        provider: Optional[str] = None,
        model: Optional[str] = None
    ) -> Tuple[str, List[Dict[str, Any]], Dict[str, Any]]:
        """
        Generate a Ship 30 for 30 essay grounded in transcript context.
        Returns (essay_markdown, source_citations, metadata).
        """
        user_prompt = (
            f"Please write a comprehensive ~1,250-word Ship 30 for 30 growth essay on the topic: '{topic_or_query}'.\n\n"
            f"{format_context_prompt(topic_or_query, candidates)}"
        )

        messages: List[LLMMessage] = []
        if history:
            messages.extend(history)
        messages.append(LLMMessage(role="user", content=user_prompt))

        response: LLMResponse = await self.router.generate(
            messages=messages,
            system_instruction=SHIP30_SYSTEM_PROMPT,
            temperature=0.6,
            max_tokens=4000,
            provider_name=provider,
            model=model
        )

        # Build source references
        sources: List[Dict[str, Any]] = []
        seen_chunks = set()
        for idx, c in enumerate(candidates, start=1):
            if c.chunk_id not in seen_chunks:
                seen_chunks.add(c.chunk_id)
                sources.append({
                    "chunk_id": c.chunk_id,
                    "source_title": c.episode_title,
                    "source_url": c.episode_url,
                    "speaker": c.speaker,
                    "source_type": "podcast_transcript",
                    "relevance_score": c.score,
                    "rank": idx,
                    "snippet": c.text[:250] + "..."
                })

        words = len(response.content.split())
        metadata = {
            "model_provider": response.model_provider,
            "model_name": response.model_name,
            "latency_ms": response.latency_ms,
            "word_count": words,
            "input_tokens": response.input_tokens,
            "output_tokens": response.output_tokens,
            "skill": "SHIP30"
        }

        logger.info(f"Ship30 essay generated ({words} words) in {response.latency_ms}ms", extra={"operation": "ship30_complete"})
        return response.content, sources, metadata


# Global Ship30 skill singleton
ship30_skill = Ship30Skill()
