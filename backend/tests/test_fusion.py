"""
Unit Tests for Reciprocal Rank Fusion (RRF)
"""
import pytest
from backend.app.rag.qdrant import RetrievalCandidate
from backend.app.rag.fusion import reciprocal_rank_fusion

def make_candidate(chunk_id: str, title: str, text: str, score: float, rank: int, method: str) -> RetrievalCandidate:
    return RetrievalCandidate(
        chunk_id=chunk_id,
        document_id="doc1",
        episode_title=title,
        text=text,
        score=score,
        rank=rank,
        retrieval_method=method
    )

def test_rrf_combines_dense_and_bm25():
    # Chunk A appears in both dense (#1) and bm25 (#1) -> should be #1 overall
    # Chunk B appears only in dense (#2)
    # Chunk C appears only in bm25 (#2)
    dense_list = [
        make_candidate("chunk_A", "Title A", "Content A", 0.95, 1, "dense"),
        make_candidate("chunk_B", "Title B", "Content B", 0.85, 2, "dense"),
    ]
    bm25_list = [
        make_candidate("chunk_A", "Title A", "Content A", 12.5, 1, "bm25"),
        make_candidate("chunk_C", "Title C", "Content C", 8.2, 2, "bm25"),
    ]

    fused = reciprocal_rank_fusion([dense_list, bm25_list], k=60, top_k=5)

    assert len(fused) == 3
    assert fused[0].chunk_id == "chunk_A"
    # Chunk A score should be 1/(60+1) + 1/(60+1) = 2/61 ~ 0.03278
    assert fused[0].score == pytest.approx(2.0 / 61.0)
    assert fused[0].rank == 1
    assert "dense" in fused[0].retrieval_method and "bm25" in fused[0].retrieval_method

def test_rrf_empty_lists():
    fused = reciprocal_rank_fusion([[], []], k=60, top_k=5)
    assert fused == []
