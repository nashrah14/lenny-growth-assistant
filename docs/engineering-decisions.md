# Architectural Decision Records (ADRs)

## Project: The Lenny Growth Assistant

---

### ADR-001: Two-Stage Hybrid Retrieval (Dense Embeddings + BM25)
- **Status**: Accepted
- **Context**: Relying solely on dense semantic search fails on specific names, framework acronyms (e.g., "PMF", "PLG", "LTV/CAC"), and guest mentions. Relying solely on lexical search fails on natural language conceptual queries.
- **Decision**: Implement parallel execution of Dense Vector Search (`sentence-transformers/all-MiniLM-L6-v2`, 384 dimensions) and BM25 Okapi lexical index.
- **Consequences**: Maximizes recall and exact match precision.

---

### ADR-002: Reciprocal Rank Fusion (RRF, k=60)
- **Status**: Accepted
- **Context**: Combining raw dense cosine distances with unbounded BM25 float scores leads to calibration skew.
- **Decision**: Use rank-based Reciprocal Rank Fusion ($RRF\_Score(d) = \sum \frac{1}{k + r_i(d)}$) with standard smoothing parameter $k=60$.
- **Consequences**: Stable, rank-invariant candidate merging.

---

### ADR-003: Cross-Encoder Reranking (`ms-marco-MiniLM-L-6-v2`)
- **Status**: Accepted
- **Context**: Bi-encoders compute query and document representations independently. A Cross-Encoder performs full cross-attention between query and candidate text.
- **Decision**: Rerank the Top-20 fused candidates down to Top-5 final context windows using `CrossEncoder`. Fall back to RRF order if model unavailable.
- **Consequences**: Highest precision context presented to the LLM.

---

### ADR-004: Relational Persistence with PostgreSQL & Alembic
- **Status**: Accepted
- **Context**: Conversational state, message history, source attributions, artifacts, and user accounts require ACID guarantees and relational integrity.
- **Decision**: Use PostgreSQL with async SQLAlchemy and Alembic migrations.
- **Consequences**: Clean separation of relational state from vector index.

---

### ADR-005: Model-Agnostic LLM Provider Layer
- **Status**: Accepted
- **Context**: The assistant must support runtime switching between Google Gemini and local/remote Ollama instances without server restart.
- **Decision**: Define an abstract `LLMProvider` interface and dynamic `LLMRouter` with automatic fallback.
- **Consequences**: High resilience and vendor flexibility.

---

### ADR-006: Multi-Layer Artifact Security & Sandboxed Iframe
- **Status**: Accepted
- **Context**: Allowing generated HTML/JS artifacts to render in user browsers creates high risk of Cross-Site Scripting (XSS) and token exfiltration.
- **Decision**: Enforce a 3-layer security model:
  1. Server-side sanitization with Bleach (stripping `<script>`, `onerror`, `javascript:` protocols).
  2. Strict Content Security Policy meta injection.
  3. Frontend sandboxed iframe with `sandbox="allow-scripts"` (strictly omitting `allow-same-origin` and `allow-top-navigation`).
- **Consequences**: Zero access to parent DOM, cookies, or browser storage.

---

### ADR-007: Speaker-Aware Semantic Chunking
- **Status**: Accepted
- **Context**: Fixed-size windowing arbitrarily cuts mid-sentence or mid-speaker turn, losing context on who said what.
- **Decision**: Chunk at ~800 characters with 120-character overlap while preserving speaker turn boundaries (`Speaker (HH:MM:SS):`).
- **Consequences**: Precise attribution and seekable timestamps.

---

### ADR-008: Deterministic Intent Routing
- **Status**: Accepted
- **Context**: Distinguish normal RAG Q&A from long-form Ship 30 atomic essays and interactive HTML artifact generation.
- **Decision**: Implement lightweight keyword/regex intent classifier with client-side explicit override.
- **Consequences**: Predictable prompt specialization with zero extra LLM routing latency.

---

### ADR-009: Strict Grounding & Anti-Hallucination Fallback
- **Status**: Accepted
- **Context**: Factual questions without transcript evidence must never be answered with generic hallucinated knowledge.
- **Decision**: Enforce strict system instructions and return deterministic fallback ("I couldn't find sufficient evidence in the Lenny transcript knowledge base to answer this reliably.") when retrieval confidence is insufficient.
- **Consequences**: 100% trustworthy answers backed by citations.

---

### ADR-010: Structured JSON Observability & Secret Redaction
- **Status**: Accepted
- **Context**: Production tracing is required without accidentally leaking API keys, passwords, or PII into logs.
- **Decision**: Custom logging formatter with regex filters masking `Bearer`, API keys, passwords, and tokens.
- **Consequences**: Safe auditability and zero credential leakage.

---

### ADR-011: OWASP-Compliant Argon2id Password Hashing & HttpOnly Session Cookies
- **Status**: Accepted
- **Context**: Modern authentication requires protection against credential brute-forcing, rainbow tables, and XSS-based token theft (localStorage is vulnerable to JavaScript access).
- **Decision**:
  1. Hash passwords using **Argon2id** (memory-hard, resistant to GPU/ASIC attacks).
  2. Issue signed JWT session tokens stored exclusively in **HttpOnly, SameSite=Lax** cookies.
  3. Enforce user ownership on all session, message, and artifact queries in PostgreSQL.
- **Consequences**: High security posture with zero client-side token exposure to JavaScript.
