"""
Transcript Dataset Ingestion Pipeline
Parses, cleans, chunks, embeds, and indexes all 300+ Lenny's Podcast transcripts idempotently.
"""
import time
import asyncio
from pathlib import Path
from typing import List, Dict, Any, Optional
from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.rag.parser import parse_transcript_file, ParsedTranscript
from backend.app.rag.chunking import TranscriptChunker, TranscriptChunk
from backend.app.rag.embeddings import embedding_provider
from backend.app.rag.qdrant import qdrant_adapter
from backend.app.rag.bm25 import bm25_index
from backend.app.db.session import AsyncSessionLocal
from backend.app.db.repositories.ingestion_repo import IngestionRepository

class IngestionReport(dict):
    """Container for ingestion execution metrics."""
    pass


class IngestionPipeline:
    def __init__(
        self,
        transcripts_dir: Optional[Path] = None,
        chunk_size: Optional[int] = None,
        chunk_overlap: Optional[int] = None
    ):
        self.transcripts_dir = Path(transcripts_dir or settings.TRANSCRIPTS_DIR)
        self.chunker = TranscriptChunker(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        self.embedding = embedding_provider
        self.qdrant = qdrant_adapter
        self.bm25 = bm25_index

    async def run(
        self,
        limit: Optional[int] = None,
        dry_run: bool = False,
        rebuild: bool = False
    ) -> Dict[str, Any]:
        start_time = time.perf_counter()
        logger.info(f"Starting transcript ingestion from {self.transcripts_dir}", extra={"operation": "ingestion_start"})

        # Record ingestion run in PostgreSQL
        run_record = None
        try:
            async with AsyncSessionLocal() as session:
                repo = IngestionRepository(session)
                run_record = await repo.start_run(metadata={"dry_run": dry_run, "rebuild": rebuild, "limit": limit})
                await session.commit()
        except Exception as e:
            logger.warning(f"Could not record ingestion start in database: {e}", extra={"operation": "db_run_record_warning"})

        if not self.transcripts_dir.exists():
            error_msg = f"Transcripts directory not found: {self.transcripts_dir}"
            logger.error(error_msg, extra={"operation": "ingestion_dir_missing"})
            if run_record:
                try:
                    async with AsyncSessionLocal() as session:
                        repo = IngestionRepository(session)
                        await repo.fail_run(run_record.id, error_msg)
                        await session.commit()
                except Exception:
                    pass
            return {"status": "FAILED", "error": error_msg}

        # Discover all transcript files
        episode_folders = [
            f for f in self.transcripts_dir.iterdir()
            if f.is_dir() and (f / "transcript.md").exists()
        ]
        if limit:
            episode_folders = episode_folders[:limit]

        total_files = len(episode_folders)
        logger.info(f"Found {total_files} episode transcripts to process", extra={"operation": "ingestion_discovery"})

        parsed_transcripts: List[ParsedTranscript] = []
        all_chunks: List[TranscriptChunk] = []
        failed_files: List[str] = []

        # Step 1: Parse transcripts and chunk
        for folder in episode_folders:
            t_path = folder / "transcript.md"
            try:
                parsed = parse_transcript_file(t_path)
                parsed_transcripts.append(parsed)
                chunks = self.chunker.chunk_transcript(parsed)
                all_chunks.extend(chunks)
            except Exception as e:
                logger.error(f"Error parsing {folder.name}: {e}", extra={"operation": "parse_error"})
                failed_files.append(folder.name)

        logger.info(f"Generated {len(all_chunks)} chunks from {len(parsed_transcripts)} transcripts", extra={"operation": "chunking_complete"})

        if dry_run:
            duration = int((time.perf_counter() - start_time) * 1000)
            return {
                "status": "DRY_RUN_COMPLETED",
                "total_documents": len(parsed_transcripts),
                "total_chunks": len(all_chunks),
                "failed_documents": len(failed_files),
                "duration_ms": duration
            }

        # Step 2: Dense Embeddings & Qdrant Upsert
        logger.info("Computing dense embeddings for chunks...", extra={"operation": "embedding_start"})
        chunk_texts = [c.text for c in all_chunks]
        vectors = await self.embedding.embed_texts_async(chunk_texts)

        logger.info(f"Generated {len(vectors)} dense embeddings. Indexing into Qdrant...", extra={"operation": "qdrant_upsert_start"})
        upserted_count = await self.qdrant.upsert_chunks(all_chunks, vectors, batch_size=100)

        # Step 3: Build and Persist BM25 Index
        logger.info("Building BM25 sparse index...", extra={"operation": "bm25_build_start"})
        bm25_count = self.bm25.build_index(all_chunks)

        duration_sec = time.perf_counter() - start_time
        logger.info(f"Ingestion pipeline completed successfully in {duration_sec:.2f}s", extra={"operation": "ingestion_success"})

        # Record completion in PostgreSQL
        if run_record:
            try:
                async with AsyncSessionLocal() as session:
                    repo = IngestionRepository(session)
                    await repo.complete_run(
                        run_id=run_record.id,
                        document_count=len(parsed_transcripts),
                        chunk_count=len(all_chunks),
                        error_summary=f"Failed {len(failed_files)} files: {failed_files[:5]}" if failed_files else None
                    )
                    await session.commit()
            except Exception as e:
                logger.warning(f"Could not record ingestion completion in database: {e}")

        return {
            "status": "COMPLETED",
            "total_documents": len(parsed_transcripts),
            "total_chunks": len(all_chunks),
            "vectors_indexed": upserted_count,
            "bm25_indexed": bm25_count,
            "failed_files": failed_files,
            "duration_seconds": round(duration_sec, 2)
        }
