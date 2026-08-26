"""
Qdrant Cloud Vector Database Adapter
Handles collection initialization, dense vector indexing, payload storage, and similarity search.
"""
import time
import asyncio
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.core.exceptions import VectorDBError
from backend.app.rag.chunking import TranscriptChunk

class RetrievalCandidate(BaseModel):
    chunk_id: str
    document_id: str
    episode_title: str
    episode_url: Optional[str] = None
    speaker: str = "Unknown"
    timestamp: str = "00:00:00"
    text: str
    score: float = 0.0
    rank: int = 1
    retrieval_method: str = "dense"  # "dense", "bm25", "hybrid"
    published_at: Optional[str] = None
    keywords: List[str] = Field(default_factory=list)


class QdrantAdapter:
    def __init__(
        self,
        url: Optional[str] = None,
        api_key: Optional[str] = None,
        collection_name: Optional[str] = None
    ):
        self.url = url or settings.QDRANT_URL
        self.api_key = api_key or settings.QDRANT_API_KEY
        self.collection_name = collection_name or settings.QDRANT_COLLECTION
        self._client = None

    def _get_client(self):
        if self._client is None:
            try:
                from qdrant_client import QdrantClient
                if self.url and self.url.strip():
                    self._client = QdrantClient(
                        url=self.url,
                        api_key=self.api_key if self.api_key and self.api_key.strip() else None,
                        timeout=settings.QDRANT_TIMEOUT
                    )
                else:
                    # In-memory client for testing or fallback
                    logger.warning("No QDRANT_URL provided; using in-memory Qdrant client", extra={"operation": "qdrant_init"})
                    self._client = QdrantClient(":memory:")
            except Exception as e:
                logger.error(f"Failed to initialize Qdrant client: {e}", extra={"operation": "qdrant_init_failed"})
                raise VectorDBError(f"Failed to connect to Qdrant: {e}")
        return self._client

    async def ensure_collection(self) -> bool:
        """Idempotently ensure collection exists with 384-dim Cosine vector configuration."""
        client = self._get_client()
        from qdrant_client.http import models

        def _sync_ensure():
            try:
                collections = client.get_collections().collections
                exists = any(c.name == self.collection_name for c in collections)
                if not exists:
                    logger.info(f"Creating Qdrant collection '{self.collection_name}' (384d, Cosine)", extra={"operation": "qdrant_create"})
                    client.create_collection(
                        collection_name=self.collection_name,
                        vectors_config=models.VectorParams(
                            size=settings.EMBEDDING_DIMENSION,
                            distance=models.Distance.COSINE
                        )
                    )
                    # Create payload indexes for fast filtering
                    try:
                        client.create_payload_index(
                            collection_name=self.collection_name,
                            field_name="document_id",
                            field_schema=models.PayloadSchemaType.KEYWORD
                        )
                    except Exception:
                        pass
                return True
            except Exception as e:
                logger.error(f"Error ensuring Qdrant collection: {e}", extra={"operation": "qdrant_ensure_failed"})
                raise VectorDBError(f"Could not ensure collection '{self.collection_name}': {e}")

        return await asyncio.to_thread(_sync_ensure)

    async def upsert_chunks(
        self,
        chunks: List[TranscriptChunk],
        vectors: List[List[float]],
        batch_size: int = 100
    ) -> int:
        """Batch upsert chunks and vectors into Qdrant collection."""
        if not chunks or not vectors or len(chunks) != len(vectors):
            return 0

        await self.ensure_collection()
        client = self._get_client()
        from qdrant_client.http import models

        def _sync_upsert():
            total = len(chunks)
            upserted = 0
            for i in range(0, total, batch_size):
                batch_chunks = chunks[i:i+batch_size]
                batch_vectors = vectors[i:i+batch_size]

                points = [
                    models.PointStruct(
                        id=chunk.chunk_id,
                        vector=vector,
                        payload={
                            "chunk_id": chunk.chunk_id,
                            "document_id": chunk.document_id,
                            "chunk_index": chunk.chunk_index,
                            "episode_title": chunk.episode_title,
                            "episode_url": chunk.episode_url,
                            "speaker": chunk.speaker,
                            "timestamp": chunk.timestamp,
                            "text": chunk.text,
                            "published_at": chunk.published_at,
                            "keywords": chunk.keywords,
                            "source_type": chunk.source_type
                        }
                    )
                    for chunk, vector in zip(batch_chunks, batch_vectors)
                ]

                client.upsert(
                    collection_name=self.collection_name,
                    points=points,
                    wait=True
                )
                upserted += len(points)
            return upserted

        return await asyncio.to_thread(_sync_upsert)

    async def search_dense(
        self,
        query_vector: List[float],
        top_k: Optional[int] = None
    ) -> List[RetrievalCandidate]:
        """Perform dense cosine similarity search in Qdrant."""
        k = top_k or settings.DENSE_TOP_K
        client = self._get_client()

        def _sync_search():
            try:
                # Use query_points or search
                if hasattr(client, "query_points"):
                    results = client.query_points(
                        collection_name=self.collection_name,
                        query=query_vector,
                        limit=k,
                        with_payload=True
                    ).points
                else:
                    results = client.search(
                        collection_name=self.collection_name,
                        query_vector=query_vector,
                        limit=k,
                        with_payload=True
                    )

                candidates = []
                for idx, point in enumerate(results, start=1):
                    payload = point.payload or {}
                    candidates.append(RetrievalCandidate(
                        chunk_id=str(payload.get("chunk_id", point.id)),
                        document_id=str(payload.get("document_id", "unknown")),
                        episode_title=str(payload.get("episode_title", "Lenny's Podcast Transcript")),
                        episode_url=payload.get("episode_url"),
                        speaker=str(payload.get("speaker", "Unknown")),
                        timestamp=str(payload.get("timestamp", "00:00:00")),
                        text=str(payload.get("text", "")),
                        score=float(point.score),
                        rank=idx,
                        retrieval_method="dense",
                        published_at=payload.get("published_at"),
                        keywords=payload.get("keywords", [])
                    ))
                return candidates
            except Exception as e:
                logger.error(f"Qdrant dense search error: {e}", extra={"operation": "qdrant_search_error"})
                return []

        return await asyncio.to_thread(_sync_search)

    async def health(self) -> Dict[str, Any]:
        """Check connection health and return collection statistics."""
        client = self._get_client()
        def _sync_health():
            try:
                info = client.get_collection(self.collection_name)
                return {
                    "status": "healthy",
                    "collection": self.collection_name,
                    "points_count": getattr(info, "points_count", getattr(info, "vectors_count", 0)),
                    "vectors_count": getattr(info, "vectors_count", 0)
                }
            except Exception as e:
                return {
                    "status": "degraded",
                    "collection": self.collection_name,
                    "error": str(e)
                }
        return await asyncio.to_thread(_sync_health)


# Global Qdrant adapter singleton
qdrant_adapter = QdrantAdapter()
