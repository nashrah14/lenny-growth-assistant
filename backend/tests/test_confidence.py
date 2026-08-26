"""
Tests for QA Confidence Scoring (Gap D)
Verifies:
  - compute_confidence returns correct levels for different evidence strengths
  - Knowledge gap detection overrides score regardless of retrieval
  - Confidence levels match documented thresholds
  - ConfidenceScore model serializes correctly
  - RAG skill metadata includes confidence
"""
import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from backend.app.agents.skills.rag import (
    compute_confidence, ConfidenceScore, ConfidenceLevel, _KNOWLEDGE_GAP_PHRASE
)


def _make_candidate(score: float, episode_title: str = "Episode A", chunk_id: str = None):
    """Helper: create a mock RetrievalCandidate."""
    c = MagicMock()
    c.score = score
    c.episode_title = episode_title
    c.chunk_id = chunk_id or f"chunk_{score}"
    return c


class TestConfidenceThresholds:
    def test_high_confidence_many_sources_high_score(self):
        candidates = [
            _make_candidate(0.85, "Ep A"),
            _make_candidate(0.80, "Ep B"),
            _make_candidate(0.75, "Ep C"),
        ]
        result = compute_confidence(candidates, "Some grounded answer text.")
        assert result.level == ConfidenceLevel.HIGH
        assert result.n_sources == 3
        assert result.top_score >= 0.70
        assert not result.knowledge_gap

    def test_moderate_confidence_two_sources_medium_score(self):
        candidates = [
            _make_candidate(0.55, "Ep A"),
            _make_candidate(0.50, "Ep B"),
        ]
        result = compute_confidence(candidates, "Some grounded answer text.")
        assert result.level == ConfidenceLevel.MODERATE
        assert result.n_sources == 2

    def test_moderate_confidence_three_plus_any_score(self):
        """3+ sources with moderate scores should still be MODERATE (not LOW)."""
        candidates = [
            _make_candidate(0.35, "Ep A"),
            _make_candidate(0.30, "Ep B"),
            _make_candidate(0.28, "Ep C"),
        ]
        result = compute_confidence(candidates, "Answer text.")
        assert result.level == ConfidenceLevel.MODERATE

    def test_low_confidence_one_source_medium_score(self):
        candidates = [_make_candidate(0.40, "Ep A")]
        result = compute_confidence(candidates, "Some grounded answer text.")
        assert result.level == ConfidenceLevel.LOW

    def test_insufficient_no_candidates(self):
        result = compute_confidence([], "Some answer text.")
        assert result.level == ConfidenceLevel.INSUFFICIENT
        assert result.n_sources == 0
        assert result.top_score == 0.0

    def test_insufficient_knowledge_gap_overrides_good_retrieval(self):
        """Even 5 high-scoring sources should be INSUFFICIENT if LLM says no evidence."""
        candidates = [
            _make_candidate(0.90, f"Ep {i}") for i in range(5)
        ]
        gap_answer = f"Unfortunately, {_KNOWLEDGE_GAP_PHRASE} to answer this reliably."
        result = compute_confidence(candidates, gap_answer)
        assert result.level == ConfidenceLevel.INSUFFICIENT
        assert result.knowledge_gap is True

    def test_low_score_single_source_insufficient(self):
        """Single source with very low reranker score → INSUFFICIENT."""
        candidates = [_make_candidate(0.10, "Ep A")]
        result = compute_confidence(candidates, "Some answer.")
        assert result.level == ConfidenceLevel.INSUFFICIENT


class TestConfidenceScoreFields:
    def test_distinct_episodes_counted(self):
        candidates = [
            _make_candidate(0.80, "Episode Alpha"),
            _make_candidate(0.75, "Episode Alpha"),  # same episode
            _make_candidate(0.70, "Episode Beta"),
        ]
        result = compute_confidence(candidates, "Answer.")
        assert result.distinct_episodes == 2  # Alpha and Beta

    def test_top_score_rounded(self):
        candidates = [_make_candidate(0.123456789, "Ep A")]
        result = compute_confidence(candidates, "Answer.")
        assert result.top_score == round(0.123456789, 4)

    def test_labels_are_defined_for_all_levels(self):
        for level in [ConfidenceLevel.HIGH, ConfidenceLevel.MODERATE,
                      ConfidenceLevel.LOW, ConfidenceLevel.INSUFFICIENT]:
            assert level in ConfidenceLevel.LABELS
            assert len(ConfidenceLevel.LABELS[level]) > 0

    def test_confidence_score_serializable(self):
        candidates = [_make_candidate(0.75, "Ep A"), _make_candidate(0.70, "Ep B"), _make_candidate(0.65, "Ep C")]
        result = compute_confidence(candidates, "A grounded answer.")
        data = result.model_dump()
        assert "level" in data
        assert "label" in data
        assert "n_sources" in data
        assert "top_score" in data
        assert "distinct_episodes" in data
        assert "knowledge_gap" in data

    def test_knowledge_gap_detection_case_insensitive(self):
        """Knowledge gap detection must work regardless of capitalization."""
        upper_gap = _KNOWLEDGE_GAP_PHRASE.upper()
        candidates = [_make_candidate(0.80, "Ep A")]
        result = compute_confidence(candidates, f"I {upper_gap.lower()} to answer.")
        assert result.knowledge_gap is True


class TestRAGSkillConfidenceIntegration:
    @pytest.mark.asyncio
    async def test_rag_skill_metadata_includes_confidence(self):
        """RAGSkill.execute() must include confidence dict in returned metadata."""
        from backend.app.agents.skills.rag import RAGSkill
        from backend.app.llm.base import LLMResponse

        skill = RAGSkill()

        candidates = [_make_candidate(0.80, "Ep A"), _make_candidate(0.75, "Ep B"), _make_candidate(0.72, "Ep C")]
        mock_response = LLMResponse(
            content="A well-grounded answer about growth.",
            model_provider="gemini",
            model_name="gemini-3.6-flash",
            latency_ms=500
        )

        with patch.object(skill.router, "generate", new=AsyncMock(return_value=mock_response)):
            content, sources, metadata = await skill.execute(
                query="How does product growth work?",
                candidates=candidates
            )

        assert "confidence" in metadata
        conf = metadata["confidence"]
        assert "level" in conf
        assert "label" in conf
        assert conf["level"] in [ConfidenceLevel.HIGH, ConfidenceLevel.MODERATE,
                                   ConfidenceLevel.LOW, ConfidenceLevel.INSUFFICIENT]

    @pytest.mark.asyncio
    async def test_rag_skill_grounded_false_when_knowledge_gap(self):
        """When LLM says no evidence, grounded=False and confidence=INSUFFICIENT."""
        from backend.app.agents.skills.rag import RAGSkill
        from backend.app.llm.base import LLMResponse

        skill = RAGSkill()
        candidates = [_make_candidate(0.90, "Ep A")]

        gap_response = LLMResponse(
            content=f"I {_KNOWLEDGE_GAP_PHRASE} to answer this query.",
            model_provider="gemini",
            model_name="gemini-3.6-flash",
            latency_ms=200
        )

        with patch.object(skill.router, "generate", new=AsyncMock(return_value=gap_response)):
            content, sources, metadata = await skill.execute(
                query="What is the meaning of life?",
                candidates=candidates
            )

        assert metadata["grounded"] is False
        assert metadata["confidence"]["level"] == ConfidenceLevel.INSUFFICIENT
        assert metadata["confidence"]["knowledge_gap"] is True
