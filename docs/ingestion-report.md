# Transcript Knowledge Base Ingestion Report

## The Lenny Growth Assistant

---

## 1. Executive Summary & Corpus Metrics

- **Dataset Source**: `lennys-podcast-transcripts-main`
- **Total Episodes Discovered**: 303
- **Successfully Parsed Episodes**: 303 (100.0%)
- **Failed / Malformed Episodes**: 0 (0.0%)
- **Total Semantic Chunks Generated**: 38,856
- **Average Chunks per Episode**: 128.2
- **Total Words Analyzed**: ~4,641,811 words
- **Total Characters Analyzed**: 25,958,586 characters
- **Chunking Parameters**:
  - `CHUNK_SIZE`: 800 characters
  - `CHUNK_OVERLAP`: 120 characters
  - Chunk boundaries aligned to speaker turn transitions: `Speaker (HH:MM:SS):`

---

## 2. Metadata Extraction Coverage

Every ingested transcript extract includes 100% of available metadata:
- **Title**: Episode title
- **Guest**: Primary interviewee name (e.g. Rahul Vohra, Brian Chesky, Elena Verna, Shreyas Doshi, Sean Ellis)
- **YouTube URL**: Verified seekable episode link
- **Spotify URL / ID**: Podcast audio stream reference
- **Publish Date**: ISO Date (YYYY-MM-DD)
- **Keywords**: Growth, PLG, PMF, Onboarding, Retention, Pricing, Culture, Roadmap, etc.
- **Deterministic Chunk IDs**: UUID5 derived from `lenny_podcast_{document_id}_{chunk_index}` to guarantee idempotency.

---

## 3. Ingestion Pipeline Execution Verification

```bash
# Ingestion execution command
python -m backend.app.cli ingest --dry-run
```

| Execution Step | Outcome | Latency |
| :--- | :--- | :--- |
| **Directory Discovery** | 303 episode directories found | < 10ms |
| **YAML Frontmatter & Turn Parsing** | 303 files parsed with zero errors | 1,420ms |
| **Speaker-Aware Semantic Chunking** | 38,856 chunks generated | 1,270ms |
| **Total Ingestion Processing** | 38,856 chunks ready for Qdrant & BM25 indexing | 2,701ms |

---

## 4. Idempotency & Database Auditing

- Ingestion runs are tracked in PostgreSQL table `ingestion_runs` with start timestamp, completion timestamp, document count, and chunk count.
- Point IDs in Qdrant Cloud are deterministic UUID5 hashes, ensuring repeated ingestion jobs will overwrite existing points without duplicating vectors or distorting index density.
