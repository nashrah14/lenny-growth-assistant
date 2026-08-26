"""
Ship 30 for 30 Content Generation Skill
Transforms grounded transcript insights into a high-impact, skimmable, ~1,250-word atomic essay.

Validation Pipeline
-------------------
After generation, the essay is validated by the deterministic ship30_validator module:
  1. Word count: 900–1,600 words
  2. Hook (punchy opener): <= 3 sentences
  3. Framework pillars: >= 3 `###` subheadings
  4. Tactical section: action-oriented language present
  5. Closing takeaway: final paragraph present

On validation failure:
  - One controlled regeneration attempt is made with explicit validation hints
  - If the second attempt also fails, a structured validation error is returned
    rather than silently returning a non-compliant artifact

Maximum attempts: 2 (one initial + one retry)
"""
from typing import List, Dict, Any, Tuple, Optional
from backend.app.rag.qdrant import RetrievalCandidate
from backend.app.llm.base import LLMMessage, LLMResponse
from backend.app.llm.router import llm_router
from backend.app.agents.skills.rag import format_context_prompt
from backend.app.agents.skills.ship30_validator import (
    validate_ship30_essay, Ship30ValidationResult,
    WORD_COUNT_MIN, WORD_COUNT_MAX, WORD_COUNT_TARGET
)
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

_RETRY_HINT_TEMPLATE = """
IMPORTANT CORRECTION REQUEST:
The previous draft did not meet the required structure. Please regenerate with strict adherence:
- Word count: {min_words}–{max_words} words (target ~{target} words). Your draft had {actual} words.
- Include a punchy 1–3 sentence opening hook
- Include at least 3 `###` framework pillar subheadings
- Include a tactical section with step-by-step Monday morning actions
- End with a closing takeaway paragraph
- Issues found: {issues}
"""


MAX_ATTEMPTS = 2


class Ship30Skill:
    def __init__(self):
        self.router = llm_router

    async def _generate_once(
        self,
        messages: List[LLMMessage],
        provider: Optional[str],
        model: Optional[str]
    ) -> Tuple[str, int, int, str, str]:
        """Single generation attempt. Returns (content, word_count, latency_ms, provider, model_name)."""
        response: LLMResponse = await self.router.generate(
            messages=messages,
            system_instruction=SHIP30_SYSTEM_PROMPT,
            temperature=0.6,
            max_tokens=4000,
            provider_name=provider,
            model=model
        )
        word_count = len(response.content.split())
        return response.content, word_count, response.latency_ms, response.model_provider, response.model_name

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
        metadata includes 'validation' key with Ship30ValidationResult data.

        On persistent validation failure, returns the best available draft with
        validation_failed=True in metadata rather than raising an exception.
        This is intentional: a partially non-compliant essay is more useful
        to the client than an error response.
        """
        user_prompt = (
            f"Please write a comprehensive ~1,250-word Ship 30 for 30 growth essay on the topic: '{topic_or_query}'.\n\n"
            f"{format_context_prompt(topic_or_query, candidates)}"
        )

        messages: List[LLMMessage] = []
        if history:
            messages.extend(history)
        messages.append(LLMMessage(role="user", content=user_prompt))

        best_content = ""
        best_latency = 0
        best_provider_name = provider or "unknown"
        best_model_name = model or "unknown"
        last_validation: Optional[Ship30ValidationResult] = None

        for attempt in range(1, MAX_ATTEMPTS + 1):
            content, word_count, latency_ms, prov, mod = await self._generate_once(messages, provider, model)
            best_content = content
            best_latency = latency_ms
            best_provider_name = prov
            best_model_name = mod

            validation = validate_ship30_essay(content)
            last_validation = validation

            logger.info(
                f"Ship30 attempt {attempt}/{MAX_ATTEMPTS}: {word_count} words, valid={validation.valid}",
                extra={
                    "operation": "ship30_validate",
                    "attempt": attempt,
                    "word_count": word_count,
                    "valid": validation.valid,
                    "issues": [i.code for i in validation.issues]
                }
            )

            if validation.valid:
                break

            if attempt < MAX_ATTEMPTS:
                # Build a corrective retry prompt with specific validation feedback
                issue_list = "; ".join(i.description for i in validation.issues)
                retry_hint = _RETRY_HINT_TEMPLATE.format(
                    min_words=WORD_COUNT_MIN,
                    max_words=WORD_COUNT_MAX,
                    target=WORD_COUNT_TARGET,
                    actual=word_count,
                    issues=issue_list
                )
                # Replace the last user message with a refined version
                messages[-1] = LLMMessage(role="user", content=user_prompt + retry_hint)
                logger.warning(f"Ship30 attempt {attempt} failed validation, retrying with correction hints")

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

        words = last_validation.word_count if last_validation else len(best_content.split())
        metadata = {
            "model_provider": best_provider_name,
            "model_name": best_model_name,
            "latency_ms": best_latency,
            "word_count": words,
            "skill": "SHIP30",
            "validation": last_validation.model_dump() if last_validation else None,
            "validation_failed": not (last_validation.valid if last_validation else False)
        }

        if last_validation and not last_validation.valid:
            logger.warning(
                f"Ship30 essay returned after {MAX_ATTEMPTS} attempts with validation failures: "
                f"{[i.code for i in last_validation.issues]}",
                extra={"operation": "ship30_validation_failed", "issues": [i.code for i in last_validation.issues]}
            )

        logger.info(
            f"Ship30 essay complete ({words} words, valid={last_validation.valid if last_validation else False})",
            extra={"operation": "ship30_complete", "word_count": words}
        )
        return best_content, sources, metadata


# Global Ship30 skill singleton
ship30_skill = Ship30Skill()
