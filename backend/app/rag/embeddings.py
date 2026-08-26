"""
Text Embedding Provider Layer
Encapsulates Dense Vector Embeddings using sentence-transformers/all-MiniLM-L6-v2 (384 dimensions).
"""
import time
import asyncio
from abc import ABC, abstractmethod
from typing import List, Optional
from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.core.exceptions import EmbeddingError

class EmbeddingProvider(ABC):
    @property
    @abstractmethod
    def dimension(self) -> int:
        """Vector dimension."""
        pass

    @abstractmethod
    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Batch encode text documents into dense vectors."""
        pass

    @abstractmethod
    def embed_query(self, query: str) -> List[float]:
        """Encode a single query string into a dense vector."""
        pass

    @abstractmethod
    async def embed_texts_async(self, texts: List[str]) -> List[List[float]]:
        """Asynchronously batch encode texts."""
        pass

    @abstractmethod
    async def embed_query_async(self, query: str) -> List[float]:
        """Asynchronously encode query."""
        pass


class SentenceTransformerEmbeddingProvider(EmbeddingProvider):
    _instance = None
    _model = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(SentenceTransformerEmbeddingProvider, cls).__new__(cls)
        return cls._instance

    def __init__(self, model_name: Optional[str] = None):
        self.model_name = model_name or settings.EMBEDDING_MODEL
        self._dim = settings.EMBEDDING_DIMENSION

    def _get_model(self):
        if SentenceTransformerEmbeddingProvider._model is None:
            logger.info(f"Loading embedding model: {self.model_name}", extra={"operation": "embedding_init"})
            try:
                from sentence_transformers import SentenceTransformer
                SentenceTransformerEmbeddingProvider._model = SentenceTransformer(self.model_name)
                # Warmup
                SentenceTransformerEmbeddingProvider._model.encode(["warmup query"])
                logger.info("Embedding model loaded successfully", extra={"operation": "embedding_ready"})
            except Exception as e:
                logger.error(f"Failed to load embedding model: {e}", extra={"operation": "embedding_load_failed"})
                raise EmbeddingError(f"Could not load SentenceTransformer model '{self.model_name}': {e}")
        return SentenceTransformerEmbeddingProvider._model

    @property
    def dimension(self) -> int:
        return self._dim

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []
        model = self._get_model()
        try:
            embeddings = model.encode(
                texts,
                batch_size=settings.EMBEDDING_BATCH_SIZE,
                show_progress_bar=False,
                normalize_embeddings=True
            )
            return embeddings.tolist()
        except Exception as e:
            raise EmbeddingError(f"Batch embedding generation failed: {e}")

    def embed_query(self, query: str) -> List[float]:
        if not query or not query.strip():
            query = "growth strategy"
        model = self._get_model()
        try:
            embedding = model.encode(
                query,
                normalize_embeddings=True,
                show_progress_bar=False
            )
            return embedding.tolist()
        except Exception as e:
            raise EmbeddingError(f"Query embedding generation failed: {e}")

    async def embed_texts_async(self, texts: List[str]) -> List[List[float]]:
        return await asyncio.to_thread(self.embed_texts, texts)

    async def embed_query_async(self, query: str) -> List[float]:
        return await asyncio.to_thread(self.embed_query, query)


# Global embedding provider singleton instance
embedding_provider = SentenceTransformerEmbeddingProvider()
