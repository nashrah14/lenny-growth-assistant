"""
Unit & Integration Tests for Skills (RAG, Ship30, Artifact)
"""
import pytest
from unittest.mock import AsyncMock, patch
from backend.app.rag.qdrant import RetrievalCandidate
from backend.app.llm.base import LLMResponse
from backend.app.agents.skills.rag import RAGSkill, format_context_prompt
from backend.app.agents.skills.ship30 import Ship30Skill
from backend.app.agents.skills.artifact import ArtifactSkill
from backend.app.artifacts.generator import extract_artifact_from_text

def make_candidate() -> RetrievalCandidate:
    return RetrievalCandidate(
        chunk_id="chunk-123",
        document_id="rahul-vohra",
        episode_title="How Superhuman Built an Engine to Find PMF",
        episode_url="https://youtube.com/watch?v=123",
        speaker="Rahul Vohra",
        timestamp="00:05:30",
        text="We asked: How would you feel if you could no longer use Superhuman? If 40% answer very disappointed, you have PMF.",
        score=0.92,
        rank=1,
        retrieval_method="dense"
    )

def test_format_context_prompt():
    cand = make_candidate()
    prompt = format_context_prompt("What is the 40% rule?", [cand])
    assert "Rahul Vohra" in prompt
    assert "Superhuman" in prompt
    assert "What is the 40% rule?" in prompt

@pytest.mark.asyncio
async def test_rag_skill_execution():
    skill = RAGSkill()
    cand = make_candidate()

    mock_llm_response = LLMResponse(
        content="According to Rahul Vohra on Lenny's podcast, PMF is measured by the 40% 'very disappointed' metric.",
        model_provider="gemini",
        model_name="gemini-1.5-flash",
        latency_ms=350,
        input_tokens=150,
        output_tokens=40
    )

    with patch.object(skill.router, "generate", new_callable=AsyncMock) as mock_gen:
        mock_gen.return_value = mock_llm_response
        answer, sources, meta = await skill.execute("What is PMF?", [cand])

        assert "Rahul Vohra" in answer
        assert len(sources) == 1
        assert sources[0]["chunk_id"] == "chunk-123"
        assert sources[0]["source_title"] == "How Superhuman Built an Engine to Find PMF"
        assert meta["grounded"] is True

@pytest.mark.asyncio
async def test_artifact_extraction_and_skill():
    sample_text = """
    Here is the CAC payback model:

    ```html
    <div id="calculator">
      <h2>CAC Payback Model</h2>
      <input type="number" id="cac" value="1000">
    </div>
    ```
    """
    artifact = extract_artifact_from_text(sample_text)
    assert artifact.artifact_type == "html"
    assert "CAC Payback Model" in artifact.title
    assert "input" in artifact.content
    assert "Content-Security-Policy" in artifact.content
