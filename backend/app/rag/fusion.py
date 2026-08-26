"""
Reciprocal Rank Fusion (RRF) Engine
Merges disparate ranked candidate lists from Dense and BM25 retrievers using rank-based fusion.
"""
from typing import List, Dict, Optional
from backend.app.core.config import settings
from backend.app.rag.qdrant import RetrievalCandidate

def reciprocal_rank_fusion(
    ranked_lists: List[List[RetrievalCandidate]],
    k: Optional[int] = None,
    top_k: Optional[int] = None
) -> List[RetrievalCandidate]:
    """
    Perform Reciprocal Rank Fusion (RRF) across multiple ranked lists.
    Formula: RRF_Score(d) = sum(1 / (k + rank_m(d))) for all lists where d appears.
    """
    rrf_k = k if k is not None else settings.RRF_K
    limit = top_k if top_k is not None else settings.RRF_TOP_K

    rrf_scores: Dict[str, float] = {}
    candidate_map: Dict[str, RetrievalCandidate] = {}
    methods_seen: Dict[str, set] = {}

    for ranked_list in ranked_lists:
        for rank, candidate in enumerate(ranked_list, start=1):
            cid = candidate.chunk_id
            if cid not in candidate_map:
                candidate_map[cid] = candidate
                methods_seen[cid] = set()

            methods_seen[cid].add(candidate.retrieval_method)
            # Add reciprocal rank score
            rrf_scores[cid] = rrf_scores.get(cid, 0.0) + (1.0 / (rrf_k + rank))

    # Sort chunk_ids by aggregated RRF score descending
    sorted_ids = sorted(rrf_scores.keys(), key=lambda cid: rrf_scores[cid], reverse=True)[:limit]

    fused_candidates: List[RetrievalCandidate] = []
    for rank, cid in enumerate(sorted_ids, start=1):
        orig = candidate_map[cid]
        methods = "+".join(sorted(list(methods_seen[cid])))
        fused_candidates.append(RetrievalCandidate(
            chunk_id=orig.chunk_id,
            document_id=orig.document_id,
            episode_title=orig.episode_title,
            episode_url=orig.episode_url,
            speaker=orig.speaker,
            timestamp=orig.timestamp,
            text=orig.text,
            score=rrf_scores[cid],
            rank=rank,
            retrieval_method=f"hybrid_rrf({methods})",
            published_at=orig.published_at,
            keywords=orig.keywords
        ))

    return fused_candidates
