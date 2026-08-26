"""
Cross-Encoder Reranker Layer
Scores (Query, Passage) pairs using cross-encoder/ms-marco-MiniLM-L-6-v2 with graceful fallback.
"""
import time
import asyncio
from typing import List, Optional
from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.rag.qdrant import RetrievalCandidate

class CrossEncoderReranker:
    _instance = None
    _model = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(CrossEncoderReranker, cls).__new__(cls)
        return cls._instance

    def __init__(self, model_name: Optional[str] = None):
        self.model_name = model_name or settings.RERANKER_MODEL
        self.enabled = settings.RERANKER_ENABLED

    def _get_model(self):
        if CrossEncoderReranker._model is None and self.enabled:
            logger.info(f"Loading cross-encoder reranker: {self.model_name}", extra={"operation": "reranker_init"})
            try:
                from sentence_transformers import CrossEncoder
                CrossEncoderReranker._model = CrossEncoder(self.model_name)
                logger.info("Cross-encoder reranker loaded successfully", extra={"operation": "reranker_ready"})
            except Exception as e:
                logger.warning(f"Could not load CrossEncoder '{self.model_name}': {e}. Reranking will fall back to RRF.", extra={"operation": "reranker_load_fallback"})
                self.enabled = False
        return CrossEncoderReranker._model

    def rerank(
        self,
        query: str,
        candidates: List[RetrievalCandidate],
        top_k: Optional[int] = None
    ) -> List[RetrievalCandidate]:
        """Rerank candidates using CrossEncoder. Falls back to original RRF order if disabled or failed."""
        k = top_k or settings.RERANK_TOP_K
        if not candidates or not self.enabled or len(candidates) <= 1:
            return candidates[:k]

        start_time = time.perf_counter()
        try:
            model = self._get_model()
            if not model:
                return candidates[:k]

            pairs = [(query, c.text) for c in candidates]
            scores = model.predict(pairs)

            # Combine candidates with reranker scores
            scored_candidates = list(zip(candidates, scores))
            # Sort descending by cross-encoder score
            scored_candidates.sort(key=lambda x: x[1], reverse=True)

            reranked: List[RetrievalCandidate] = []
            for rank, (cand, score) in enumerate(scored_candidates[:k], start=1):
                reranked.append(RetrievalCandidate(
                    chunk_id=cand.chunk_id,
                    document_id=cand.document_id,
                    episode_title=cand.episode_title,
                    episode_url=cand.episode_url,
                    speaker=cand.speaker,
                    timestamp=cand.timestamp,
                    text=cand.text,
                    score=float(score),
                    rank=rank,
                    retrieval_method=f"{cand.retrieval_method}+reranked",
                    published_at=cand.published_at,
                    keywords=cand.keywords
                ))

            latency_ms = int((time.perf_counter() - start_time) * 1000)
            logger.info(
                f"Reranked {len(candidates)} candidates to top {len(reranked)} in {latency_ms}ms",
                extra={"operation": "rerank", "latency_ms": latency_ms}
            )
            return reranked

        except Exception as e:
            logger.warning(
                f"Reranker failed: {e}. Falling back to RRF ordering.",
                extra={"operation": "rerank_fallback", "error": str(e)}
            )
            return candidates[:k]

    async def rerank_async(
        self,
        query: str,
        candidates: List[RetrievalCandidate],
        top_k: Optional[int] = None
    ) -> List[RetrievalCandidate]:
        return await asyncio.to_thread(self.rerank, query, candidates, top_k)


# Global reranker singleton instance
cross_encoder_reranker = CrossEncoderReranker()
