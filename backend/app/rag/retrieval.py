"""
Hybrid Retrieval Orchestrator
Coordinates parallel Dense + BM25 search, Reciprocal Rank Fusion, and Cross-Encoder Reranking.
"""
import time
import asyncio
from typing import List, Optional
from pydantic import BaseModel, Field
from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.rag.embeddings import embedding_provider
from backend.app.rag.qdrant import qdrant_adapter, RetrievalCandidate
from backend.app.rag.bm25 import bm25_index
from backend.app.rag.fusion import reciprocal_rank_fusion
from backend.app.rag.reranker import cross_encoder_reranker

class RetrievalDiagnostics(BaseModel):
    query: str
    dense_latency_ms: int = 0
    bm25_latency_ms: int = 0
    rrf_latency_ms: int = 0
    rerank_latency_ms: int = 0
    total_latency_ms: int = 0
    dense_candidate_count: int = 0
    bm25_candidate_count: int = 0
    fused_candidate_count: int = 0
    final_context_count: int = 0


class HybridRetrievalResult(BaseModel):
    candidates: List[RetrievalCandidate] = Field(default_factory=list)
    diagnostics: RetrievalDiagnostics


class HybridRetrievalEngine:
    def __init__(self):
        self.embedding = embedding_provider
        self.qdrant = qdrant_adapter
        self.bm25 = bm25_index
        self.reranker = cross_encoder_reranker

    async def retrieve(
        self,
        query: str,
        dense_k: Optional[int] = None,
        bm25_k: Optional[int] = None,
        rrf_top_k: Optional[int] = None,
        rerank_top_k: Optional[int] = None
    ) -> HybridRetrievalResult:
        start_total = time.perf_counter()
        k_dense = dense_k or settings.DENSE_TOP_K
        k_bm25 = bm25_k or settings.BM25_TOP_K
        k_rrf = rrf_top_k or settings.RRF_TOP_K
        k_final = rerank_top_k or settings.RERANK_TOP_K

        # Step 1: Parallel execution of Dense Search and BM25 Search
        async def _dense_search() -> tuple[List[RetrievalCandidate], int]:
            t0 = time.perf_counter()
            query_vector = await self.embedding.embed_query_async(query)
            candidates = await self.qdrant.search_dense(query_vector, top_k=k_dense)
            lat = int((time.perf_counter() - t0) * 1000)
            return candidates, lat

        async def _bm25_search() -> tuple[List[RetrievalCandidate], int]:
            t0 = time.perf_counter()
            candidates = await self.bm25.search_async(query, top_k=k_bm25)
            lat = int((time.perf_counter() - t0) * 1000)
            return candidates, lat

        (dense_results, dense_lat), (bm25_results, bm25_lat) = await asyncio.gather(
            _dense_search(),
            _bm25_search(),
            return_exceptions=False
        )

        # Step 2: Reciprocal Rank Fusion (RRF)
        t_rrf_0 = time.perf_counter()
        fused_candidates = reciprocal_rank_fusion(
            ranked_lists=[dense_results, bm25_results],
            k=settings.RRF_K,
            top_k=k_rrf
        )
        rrf_lat = int((time.perf_counter() - t_rrf_0) * 1000)

        # Step 3: Cross-Encoder Reranking
        t_rerank_0 = time.perf_counter()
        final_candidates = await self.reranker.rerank_async(
            query=query,
            candidates=fused_candidates,
            top_k=k_final
        )
        rerank_lat = int((time.perf_counter() - t_rerank_0) * 1000)

        total_lat = int((time.perf_counter() - start_total) * 1000)

        diagnostics = RetrievalDiagnostics(
            query=query,
            dense_latency_ms=dense_lat,
            bm25_latency_ms=bm25_lat,
            rrf_latency_ms=rrf_lat,
            rerank_latency_ms=rerank_lat,
            total_latency_ms=total_lat,
            dense_candidate_count=len(dense_results),
            bm25_candidate_count=len(bm25_results),
            fused_candidate_count=len(fused_candidates),
            final_context_count=len(final_candidates)
        )

        logger.info(
            f"Hybrid retrieval finished in {total_lat}ms (Dense: {len(dense_results)} in {dense_lat}ms, BM25: {len(bm25_results)} in {bm25_lat}ms, Reranked: {len(final_candidates)})",
            extra={
                "operation": "hybrid_retrieval",
                "total_latency_ms": total_lat,
                "dense_latency_ms": dense_lat,
                "bm25_latency_ms": bm25_lat,
                "rerank_latency_ms": rerank_lat,
                "final_count": len(final_candidates)
            }
        )

        return HybridRetrievalResult(
            candidates=final_candidates,
            diagnostics=diagnostics
        )


# Global retrieval engine singleton instance
retrieval_engine = HybridRetrievalEngine()
