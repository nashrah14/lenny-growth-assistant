"""
Artifact Generation Skill
Synthesizes interactive HTML/CSS/JS components or deep Markdown strategy documents.
"""
from typing import List, Dict, Any, Tuple, Optional
from backend.app.rag.qdrant import RetrievalCandidate
from backend.app.llm.base import LLMMessage, LLMResponse
from backend.app.llm.router import llm_router
from backend.app.artifacts.generator import extract_artifact_from_text, GeneratedArtifact
from backend.app.agents.skills.rag import format_context_prompt
from backend.app.core.logging import logger

ARTIFACT_SYSTEM_PROMPT = """You are an elite product designer, growth engineer, and visual architect for "The Lenny Growth Assistant".
Your primary mandate is to ALWAYS generate and render the complete, high-quality, production-ready interactive HTML/CSS or Markdown artifact requested by the user.

CRITICAL GENERATION RULES:
1. ALWAYS PRODUCE THE COMPLETE ARTIFACT: Under NO circumstances should you refuse, state "I couldn't find sufficient evidence", or output only commentary. You MUST synthesize and build the complete, functional artifact.
2. WEAVE IN PODCAST INSIGHTS: Ground the copy, metrics, frameworks (e.g. CAC Payback, Activation Rates, Time-to-Value, LTV, Retention Curves, Onboarding Funnels, PMF signals), and guest methodologies (e.g. Elena Verna, Brian Chesky, Sean Ellis, Todd Jackson, Bob Moesta) from the reference context directly into the artifact.
3. FOR HTML/CSS/JS ARTIFACTS:
   - Provide a complete, self-contained `<!DOCTYPE html>` block wrapped inside ```html ```.
   - Include modern, polished CSS (dark theme, glassmorphism, responsive flex/grid layouts, clean typography, badges, stat cards, interactive hover states).
   - Include vanilla JavaScript inside `<script>` tags for real-time interactive calculations, sliders, toggles, tab switching, or onboarding walkthrough steps.
4. FOR MARKDOWN ARTIFACTS:
   - Provide a comprehensive, structured strategy document, framework teardown, or playbook wrapped inside ```markdown ```.
5. CONVERSATIONAL INTRO: Provide a 1–2 sentence friendly overview in your chat response explaining the artifact built and highlighting key features.
"""

def format_artifact_context(candidates: List[RetrievalCandidate]) -> str:
    if not candidates:
        return ""
    blocks = []
    for idx, c in enumerate(candidates, start=1):
        blocks.append(
            f"--- Reference Transcript Excerpt {idx} ---\n"
            f"Episode: {c.episode_title}\n"
            f"Speaker: {c.speaker}\n"
            f"Content:\n{c.text}\n"
        )
    return "Podcast Transcript Insights & Frameworks (Integrate these concepts into the artifact):\n" + "\n".join(blocks)

class ArtifactSkill:
    def __init__(self):
        self.router = llm_router

    async def execute(
        self,
        prompt: str,
        candidates: List[RetrievalCandidate],
        history: Optional[List[LLMMessage]] = None,
        provider: Optional[str] = None,
        model: Optional[str] = None
    ) -> Tuple[str, Optional[GeneratedArtifact], List[Dict[str, Any]], Dict[str, Any]]:
        """
        Execute artifact generation.
        Returns (conversational_text, generated_artifact, source_citations, metadata).
        """
        context_str = format_artifact_context(candidates)
        user_prompt = f"User Request: {prompt}\n\n"
        if context_str:
            user_prompt += f"{context_str}\n\n"
        user_prompt += "Please build and render the requested complete artifact now."

        messages: List[LLMMessage] = []
        if history:
            messages.extend(history)
        messages.append(LLMMessage(role="user", content=user_prompt))

        response: LLMResponse = await self.router.generate(
            messages=messages,
            system_instruction=ARTIFACT_SYSTEM_PROMPT,
            temperature=0.4,
            max_tokens=4000,
            provider_name=provider,
            model=model
        )

        # Extract artifact
        artifact = extract_artifact_from_text(response.content, default_title="Growth Artifact")

        # Conversational summary text (strip big code blocks from chat text for clean readability)
        chat_text = response.content
        if "```html" in chat_text:
            chat_text = chat_text.split("```html")[0].strip()
            if not chat_text:
                chat_text = f"I've generated the **{artifact.title}** artifact for you. You can interact with it in the Artifact Viewer on the right."
        elif "```markdown" in chat_text:
            chat_text = chat_text.split("```markdown")[0].strip()
            if not chat_text:
                chat_text = f"I've generated the **{artifact.title}** strategy artifact in the viewer on the right."

        # Source references
        sources: List[Dict[str, Any]] = []
        for idx, c in enumerate(candidates, start=1):
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

        metadata = {
            "model_provider": response.model_provider,
            "model_name": response.model_name,
            "latency_ms": response.latency_ms,
            "artifact_type": artifact.artifact_type,
            "artifact_title": artifact.title,
            "skill": "ARTIFACT"
        }

        logger.info(f"Artifact '{artifact.title}' ({artifact.artifact_type}) generated in {response.latency_ms}ms", extra={"operation": "artifact_generated"})
        return chat_text, artifact, sources, metadata


# Global artifact skill singleton
artifact_skill = ArtifactSkill()
