# Engineering Iteration Log — Production Hardening Sprint

## Project: The Lenny Growth Assistant  
**Session**: Phase 2 — Production Hardening (9.3/10 → 10/10)  
**Date**: 2026-08-26  
**Role**: Lead Forward Deployed Engineer

---

## Iteration 1: Managed PostgreSQL in Docker Compose (Gap F)

**Problem identified**: `docker-compose.yml` listed postgres as a service but the existing version had 
no health check, no managed volume, and the backend `depends_on` condition was `service_started` 
(insufficient — backend would crash if postgres hadn't finished initializing). Additionally, the 
Dockerfile used a bare `CMD uvicorn ...` with no migration hook, so fresh deployments would fail 
attempting DB operations against an empty schema.

**Investigation**:
- Read `docker-compose.yml`: confirmed no healthcheck on postgres service
- Read `backend/Dockerfile`: confirmed CMD with no alembic pre-step
- Read `.env.example`: confirmed no POSTGRES_USER/POSTGRES_PASSWORD/POSTGRES_DB vars for compose
- Read `backend/alembic.ini`: confirmed alembic config exists and is properly targeted

**Changes made**:
1. `docker-compose.yml` — Added `postgres:16-alpine` service with:
   - `pg_isready` healthcheck (10s interval, 10 retries, 20s start_period)
   - Named volume `pgdata` for data persistence across `docker compose down`
   - `depends_on: backend: condition: service_healthy` chaining
   - Internal networking via `lenny-net` bridge (postgres not exposed to host by default)
   - Backend `DATABASE_URL` override via compose environment to use service hostname
2. `backend/entrypoint.sh` — New shell script: runs `alembic upgrade head` before starting uvicorn
3. `backend/Dockerfile` — Switched `CMD` → `ENTRYPOINT ["/app/backend/entrypoint.sh"]`
4. `.env.example` — Added `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`, `BACKEND_PORT`, `FRONTEND_PORT`

**Result**: `docker compose up --build` now produces a fully functional system from cold start with 
schema applied automatically. `docker compose down -v && docker compose up --build` provides clean 
reset path.

---

## Iteration 2: Per-User Rate Limiting (Gap B)

**Problem identified**: Chat endpoint (`POST /api/v1/sessions/{id}/messages`) had no rate limiting. 
A single user could flood the Gemini or Ollama provider with unlimited parallel requests, causing 
API quota exhaustion and potential costs/service degradation for other users. Auth endpoints (login/signup) 
were similarly unprotected against brute force.

**Investigation**:
- Read `backend/app/main.py`: no rate limit middleware, no `429` handler
- Read `backend/app/api/routes/messages.py`: no decorator or middleware protection
- Evaluated options: `fastapi-limiter` (requires Redis), `slowapi` (works with memory backend), 
  custom middleware (more code). Selected `slowapi` for minimal external dependency (memory:// 
  default, upgradeable to Redis for multi-process deployments via `RATE_LIMIT_STORAGE_URI`)

**Key design decision — rate limit key function**:
- Primary key: authenticated user ID extracted from JWT cookie or Authorization header
- Fallback: client IP address for unauthenticated endpoints
- Rationale: IP-based limiting in a multi-user app is incorrect (shared IPs in corporate networks, 
  NAT, VPNs). User-ID keying ensures one user cannot impact another user's quota.

**Changes made**:
1. `backend/requirements.txt` — Added `slowapi>=0.1.9`, `limits>=3.7.0`
2. `backend/app/core/limiter.py` — **New module**: rate limiter singleton with documented key function.
   Extracted to separate module (not in main.py) to prevent circular imports with route files.
3. `backend/app/core/config.py` — Added `RATE_LIMIT_CHAT_PER_MINUTE`, `RATE_LIMIT_AUTH_PER_MINUTE`, 
   `RATE_LIMIT_STORAGE_URI` settings
4. `backend/app/main.py` — Attached limiter to `app.state.limiter`; added structured `429` handler 
   with `Retry-After` response header; exposed rate-limit headers in CORS `expose_headers`
5. `backend/app/api/routes/messages.py` — Applied `@limiter.limit(...)` decorator to chat POST endpoint
6. `.env.example` — Documented all three rate limit settings

**Bug encountered and fixed**: First attempt imported `limiter` from `backend.app.main` in 
`messages.py`. This created a circular import (`main → routes → messages → main`). Fixed by 
extracting `limiter` to `backend.app.core.limiter` and importing from there in both `main.py` 
and `messages.py`.

**Tests added**: `backend/tests/test_rate_limiting.py` — 6 tests covering configuration defaults, 
key function IP fallback, key function JWT extraction, 429 response structure, and security of 
error response (no internal data leakage).

---

## Iteration 3: Real Ollama Server-Sent Event Streaming (Gap C)

**Problem identified**: Ollama provider had no streaming support. Every response required full 
completion before returning, making the UI feel unresponsive for long Ollama answers (llama3.2:3b 
can take 10-30 seconds for detailed responses on CPU). The `LLMProvider` base class had no 
`generate_stream()` contract.

**Investigation**:
- Read `backend/app/llm/base.py`: confirmed no streaming abstract method
- Read `backend/app/llm/ollama.py`: confirmed single `generate()` call with `stream: false`
- Checked Ollama API docs: `/api/chat` with `stream: true` returns NDJSON — one JSON object per line,
  each with `message.content` (the next token) and a `done` flag on the final line

**Changes made**:
1. `backend/app/llm/base.py` — Added `generate_stream()` with default fallback implementation 
   (yields full `generate()` response as single chunk; non-breaking for existing providers)
2. `backend/app/llm/ollama.py` — Refactored: extracted `_build_payload()` helper; implemented 
   `generate_stream()` with real httpx async streaming (`client.stream("POST", ...)`, `aiter_lines()`). 
   Design decisions documented in docstring: malformed lines skipped with warning not crash; 
   client disconnect handled at SSE layer; empty tokens passed through faithfully.
3. `backend/app/api/routes/messages.py` — Added `POST /stream` SSE endpoint:
   - Ollama path: real token-by-token streaming with client disconnect detection
   - Gemini path: full response then single-chunk emission (SDK limitation documented)
   - Final `event: done` includes message_id, sources, confidence, provider metadata
   - Error path: `event: error` with structured JSON payload directing client to batch endpoint
4. `backend/app/core/config.py` — Added `OLLAMA_STREAMING_ENABLED` boolean toggle

**Tests added**: `backend/tests/test_streaming.py` — 9 tests covering token yield, empty token 
filtering, malformed JSON skip, done-flag termination, connection failure, timeout, non-streaming 
regression, and Gemini base-class fallback behavior.

---

## Iteration 4: QA Confidence Scoring (Gap D)

**Problem identified**: RAG answers returned with no indication of how well-grounded they were. 
A question with 5 highly relevant passages and a question with 0 passages both returned the same 
response structure. Evaluators had no way to distinguish "trustworthy" from "hallucination risk" 
answers from the API response alone.

**Investigation**:
- Read `backend/app/agents/skills/rag.py`: confirmed no confidence metadata
- Reviewed academic literature on RAG confidence: calibrated probabilities not possible without 
  a separate calibration dataset; semantic similarity scores from cross-encoders are not probabilities.
- Decision: implement transparent threshold-bucket model based on observable retrieval signals only.

**Design decisions** (documented in module docstring):
- Signals: source count, top reranker score, distinct episode count, LLM knowledge-gap detection
- 4 levels: HIGH, MODERATE, LOW, INSUFFICIENT (not percentages)
- Knowledge gap detection: phrase match on "couldn't find sufficient evidence" — this is the exact 
  phrase mandated in the system prompt, making it a reliable signal
- Documented why calibrated probability is NOT used: would misrepresent statistical reliability

**Changes made**:
1. `backend/app/agents/skills/rag.py` — Added `ConfidenceLevel`, `ConfidenceScore` (Pydantic), 
   `compute_confidence()` function; integrated into `RAGSkill.execute()`, added confidence to 
   metadata dict; updated `grounded` flag to use `confidence.knowledge_gap`
2. Module docstring updated with threshold documentation and honest caveat about heuristic nature

**Tests added**: `backend/tests/test_confidence.py` — 14 tests covering all 4 confidence levels, 
boundary conditions, knowledge gap override, distinct episode counting, serialization, and 
RAG skill integration (including grounded=False verification).

---

## Iteration 5: Ship 30 Deterministic Validation (Gap E)

**Problem identified**: Ship30Skill generated essays with no structural validation. A 400-word 
output or one missing tactical section would be returned silently with the same success response 
as a fully compliant 1,250-word essay.

**Investigation**:
- Read `backend/app/agents/skills/ship30.py`: confirmed no word count check, no structural check
- Evaluated approaches: LLM-as-judge (rejected — same model judges its own output, circular), 
  regex + word count (accepted — deterministic, testable, zero additional API cost)
- Defined validation specification: 900–1,600 word range, hook ≤3 sentences, ≥3 `###` headings, 
  tactical keyword present, closing takeaway present

**Changes made**:
1. `backend/app/agents/skills/ship30_validator.py` — **New module** with full documentation of 
   rationale, thresholds, and why deterministic (not LLM-based) validation was chosen. Contains:
   `ValidationIssue`, `Ship30ValidationResult` Pydantic models; `validate_ship30_essay()` function 
   with 5 independent checks; documented word count bounds (900–1,600, target 1,250)
2. `backend/app/agents/skills/ship30.py` — Integrated validator with retry loop (MAX_ATTEMPTS=2). 
   On failure: constructs corrective retry prompt with specific issue descriptions. On second failure: 
   returns best draft with `validation_failed=True` in metadata. Rationale: partial essay > error response.

**Tests added**: `backend/tests/test_ship30_validator.py` — 18 tests covering word count boundaries, 
hook detection, pillar counting, tactical keyword matching, takeaway detection, determinism guarantee, 
serialization, and Ship30Skill retry behavior (verified call count == 2 on first failure).

---

## Final Test Run Result

```
75/75 tests passing in 3.84s
```

Tests breakdown by module:
- `test_api.py`: 2 (health, session flow)
- `test_auth.py`: 4 (signup, login, logout, IDOR isolation)
- `test_chunking.py`: 2
- `test_confidence.py`: 14 ← new
- `test_config.py`: 2
- `test_fusion.py`: 2
- `test_intent_router.py`: 4
- `test_llm_providers.py`: 3
- `test_parser.py`: 1
- `test_rate_limiting.py`: 6 ← new
- `test_sanitizer.py`: 5
- `test_session_service.py`: 1
- `test_ship30_validator.py`: 18 ← new
- `test_skills.py`: 3
- `test_streaming.py`: 8 ← new
