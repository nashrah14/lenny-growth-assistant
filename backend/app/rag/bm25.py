"""
BM25 Lexical Retrieval Engine
Provides exact-match keyword, guest name, framework, and entity retrieval using BM25Okapi.
"""
import re
import pickle
import asyncio
from pathlib import Path
from typing import List, Optional, Dict, Any
from backend.app.core.config import settings, WORKSPACE_ROOT
from backend.app.core.logging import logger
from backend.app.rag.chunking import TranscriptChunk
from backend.app.rag.qdrant import RetrievalCandidate

STOPWORDS = {
    "a", "about", "above", "after", "again", "against", "all", "am", "an", "and", "any", "are",
    "as", "at", "be", "because", "been", "before", "being", "below", "between", "both", "but",
    "by", "could", "did", "do", "does", "doing", "down", "during", "each", "few", "for", "from",
    "further", "had", "has", "have", "having", "he", "her", "here", "hers", "herself", "him",
    "himself", "his", "how", "i", "if", "in", "into", "is", "it", "its", "itself", "just", "me",
    "more", "most", "my", "myself", "no", "nor", "not", "of", "off", "on", "once", "only", "or",
    "other", "ought", "our", "ours", "ourselves", "out", "over", "own", "same", "she", "should",
    "so", "some", "such", "than", "that", "the", "their", "theirs", "them", "themselves", "then",
    "there", "these", "they", "this", "those", "through", "to", "too", "under", "until", "up",
    "very", "was", "we", "were", "what", "when", "where", "which", "while", "who", "whom", "why",
    "with", "would", "you", "your", "yours", "yourself", "yourselves"
}

def tokenize(text: str) -> List[str]:
    """Tokenize, lowercase, and filter stopwords for lexical matching."""
    tokens = re.findall(r'\b[A-Za-z0-9_\-]+\b', text.lower())
    return [t for t in tokens if t not in STOPWORDS and len(t) > 1]


class BM25Index:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(BM25Index, cls).__new__(cls)
        return cls._instance

    def __init__(self, index_path: Optional[Path] = None):
        self.index_path = index_path or (WORKSPACE_ROOT / "data" / "processed" / "bm25_index.pkl")
        self.chunks: List[TranscriptChunk] = []
        self.tokenized_corpus: List[List[str]] = []
        self._bm25 = None
        self._load_if_exists()

    def _load_if_exists(self):
        if self.index_path.exists() and not self.chunks:
            try:
                with open(self.index_path, "rb") as f:
                    data = pickle.load(f)
                    self.chunks = data.get("chunks", [])
                    self.tokenized_corpus = data.get("tokenized_corpus", [])
                    from rank_bm25 import BM25Okapi
                    if self.tokenized_corpus:
                        self._bm25 = BM25Okapi(self.tokenized_corpus)
                        logger.info(f"Loaded existing BM25 index with {len(self.chunks)} chunks", extra={"operation": "bm25_load"})
            except Exception as e:
                logger.warning(f"Could not load BM25 index from cache: {e}", extra={"operation": "bm25_cache_miss"})

    def build_index(self, chunks: List[TranscriptChunk]) -> int:
        """Build and persist BM25 index from transcript chunks."""
        from rank_bm25 import BM25Okapi
        self.chunks = chunks
        self.tokenized_corpus = []

        for chunk in chunks:
            # Combine title, speaker, keywords, and text for rich lexical representation
            full_text = f"{chunk.episode_title} {chunk.speaker} {' '.join(chunk.keywords)} {chunk.text}"
            self.tokenized_corpus.append(tokenize(full_text))

        if self.tokenized_corpus:
            self._bm25 = BM25Okapi(self.tokenized_corpus)
            self._save()
            logger.info(f"Built BM25 index with {len(chunks)} chunks", extra={"operation": "bm25_build"})
        return len(chunks)

    def _save(self):
        try:
            self.index_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.index_path, "wb") as f:
                pickle.dump({
                    "chunks": self.chunks,
                    "tokenized_corpus": self.tokenized_corpus
                }, f)
        except Exception as e:
            logger.error(f"Failed to persist BM25 index: {e}", extra={"operation": "bm25_save_failed"})

    def search(self, query: str, top_k: Optional[int] = None) -> List[RetrievalCandidate]:
        """Query BM25 index and return Top-K lexical candidates."""
        k = top_k or settings.BM25_TOP_K
        if not self._bm25 or not self.chunks:
            return []

        query_tokens = tokenize(query)
        if not query_tokens:
            return []

        scores = self._bm25.get_scores(query_tokens)
        top_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:k]

        candidates: List[RetrievalCandidate] = []
        for rank, idx in enumerate(top_indices, start=1):
            score = float(scores[idx])
            if score <= 0:
                continue
            chunk = self.chunks[idx]
            candidates.append(RetrievalCandidate(
                chunk_id=chunk.chunk_id,
                document_id=chunk.document_id,
                episode_title=chunk.episode_title,
                episode_url=chunk.episode_url,
                speaker=chunk.speaker,
                timestamp=chunk.timestamp,
                text=chunk.text,
                score=score,
                rank=rank,
                retrieval_method="bm25",
                published_at=chunk.published_at,
                keywords=chunk.keywords
            ))
        return candidates

    async def search_async(self, query: str, top_k: Optional[int] = None) -> List[RetrievalCandidate]:
        return await asyncio.to_thread(self.search, query, top_k)


# Global BM25 index singleton instance
bm25_index = BM25Index()
