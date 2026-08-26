# Product Requirements Document (PRD)

## Project: The Lenny Growth Assistant
**Author**: Lead Forward Deployed Engineer & Technical Architect  
**Target Milestone**: Production Local Deployment & Hiring Assessment Submission  
**Status**: Ready for Implementation  

---

## 1. Executive Summary & Discovery Brief

### 1.1 The User & The Problem
- **Target Persona**: Product Managers, Growth Leads, Founders, and Product Marketing Managers seeking authoritative, nuanced growth playbooks and strategies.
- **The Core Problem**: Lenny Rachitsky's podcast contains 300+ episodes featuring world-class leaders (Brian Chesky, Elena Verna, Shreyas Doshi, Sean Ellis, Gustaf Alströmer, Julie Zhuo, etc.). This repository contains ~4.6M words of gold-standard product knowledge. However, finding precise frameworks, conflicting viewpoints, and actionable tactical steps requires hours of audio listening or fragmented search.
- **The Job-to-be-Done (JTBD)**: *"When I am developing a growth strategy or product framework, I want to query Lenny's interview knowledge base to get directly grounded answers with exact citations, turn them into executive essays, and visualize frameworks as interactive artifacts without wrestling with prompts or infrastructure."*

### 1.2 Success Metrics
1. **Source Grounding Rate**: 100% of factual claims cite verified episode titles, speaker identities, and YouTube/Spotify source links with zero fabricated citations.
2. **Retrieval Precision**: Mean Reciprocal Rank (MRR) > 0.85 across test benchmark queries combining semantic concepts and exact proper names.
3. **Sub-second Response Time**: Average retrieval pipeline latency (Dense + BM25 + RRF + Reranker) under 250ms on standard developer hardware.
4. **Zero-Execution Sandbox Security**: 0% XSS escape or unauthorized DOM/network egress from rendered HTML artifacts.

### 1.3 Assumptions
- Transcripts are clean markdown files with structured YAML frontmatter (metadata: title, guest, date, urls).
- Evaluation environment provides either local PostgreSQL or Docker, and access to either Google Gemini API key or a local/remote Ollama instance.
- Users value deterministic answers backed by real evidence over speculative or ungrounded generative hallucinations.

### 1.4 Scope Choices

| Feature Area | In Scope | Out of Scope | Rationale |
| :--- | :--- | :--- | :--- |
| **Knowledge Base** | 303 episodes of Lenny's Podcast transcripts with full metadata | Audio/video transcription from scratch | Transcripts are already curated and verified in repository |
| **Retrieval Engine** | Hybrid Dense (MiniLM-L6-v2) + BM25 + RRF + Cross-Encoder Reranker | Full external internet search | Focus is strict grounding within Lenny's expert domain |
| **LLM Support** | Google Gemini (`google-genai`) and Remote Ollama | Proprietary paid APIs requiring custom VPNs | Ensures reproducible evaluation on any machine |
| **Agent / Skills** | Grounded Q&A, Ship 30 for 30 Essay, Artifact Generation | Autonomous infinite multi-agent loops | Prevents nondeterministic loops and excessive latency |
| **Artifacts** | Markdown docs, interactive HTML/CSS components with sandboxed viewer | Full backend code execution sandbox (e.g. Python REPL) | Eliminates server-side remote code execution risks |

### 1.5 Risks & Mitigations

| Risk | Impact | Likelihood | Mitigation Strategy |
| :--- | :--- | :--- | :--- |
| **Hallucination / Fake Citations** | High | Medium | Strict system instructions requiring verbatim quotation references and rejection fallback when evidence is insufficient. |
| **XSS via Generated HTML** | Critical | Medium | Dual-layer defense: Server-side sanitization (`bleach`) + sandboxed `<iframe>` with strict CSP and no parent-window access. |
| **Ollama Service Timeout** | Medium | Medium | Configurable timeout (120s), graceful retry, and automatic fallback to cloud provider or informative user error. |
| **High Vector Ingestion Cost** | Low | Low | Free, local `all-MiniLM-L6-v2` dense model; zero per-token embedding API costs; batch upserts to Qdrant. |

---

## 2. User Stories & Acceptance Criteria

### US-01: Grounded Conversational Q&A
- **As a** Growth Lead,
- **I want to** ask questions like *"What is the Superhuman PMF engine and how did Rahul Vohra measure it?"*,
- **So that** I get an authoritative answer explaining the exact 40% "very disappointed" rule, survey questions, and segment segmentation, with links to Rahul Vohra's episode.
- **Acceptance Criteria**:
  - Response contains clear, structured answer.
  - Source panel shows episode title, guest name, timestamp/offset, and YouTube link.
  - If a query is unrelated (e.g. *"What is quantum entanglement?"*), the assistant cleanly responds: *"I couldn't find sufficient evidence in the Lenny transcript knowledge base to answer this reliably."*

### US-02: Ship 30 for 30 Content Generation
- **As a** Product Marketer or Founder,
- **I want to** convert Lenny's insights on viral loops or retention into a ~1,250-word Ship 30 for 30 atomic essay,
- **So that** I can publish high-signal, skimmable thought leadership for my team or social audience.
- **Acceptance Criteria**:
  - Essay follows Ship 30 format: 1-sentence hook, clear problem agitation, 3-5 core framework pillars with bold emphasis, tactical execution steps, and closing takeaway.
  - Word count targets ~1,250 words.
  - All frameworks are attributed to the relevant podcast guests.

### US-03: Artifact Generation & Interactive Viewer
- **As a** Product Manager,
- **I want to** ask for a growth model calculator or product launch checklist,
- **So that** the assistant renders a live, interactive HTML/CSS tool or Markdown artifact in the split-screen panel.
- **Acceptance Criteria**:
  - Artifact renders smoothly in the right-hand Artifact Viewer panel without blocking the chat.
  - Tabs allow toggling between Live Rendered Preview and Raw Source Code.
  - User can copy artifact code or export it.
  - Malicious script tags or event handlers are stripped before rendering.

### US-04: Session Isolation & History Preservation
- **As a** User,
- **I want to** manage multiple independent chat sessions in the sidebar,
- **So that** my conversation about B2B pricing does not bleed into my conversation about onboarding flows.
- **Acceptance Criteria**:
  - New Chat button generates isolated session.
  - Sidebar lists all historical sessions with titles and timestamps.
  - Switching sessions updates conversation state immediately.

### US-05: Dynamic LLM Model Switcher
- **As an** Evaluator,
- **I want to** switch between Google Gemini and local/remote Ollama in the UI header,
- **So that** I can test both cloud and local model performance instantly.
- **Acceptance Criteria**:
  - Model indicator in header displays active provider and model name.
  - Switching provider applies to subsequent messages without restarting the server.

---

## 3. Product Architecture Overview

```
+-----------------------------------------------------------------------------------+
|                                 React + TypeScript UI                             |
|  +---------------------+  +--------------------------------+  +-----------------+  |
|  |  Session Sidebar    |  |       Conversation Stream      |  | Artifact Viewer |  |
|  |  - New Session      |  |  - Grounded Markdown Responses |  | - Live Preview  |  |
|  |  - Session History  |  |  - Source Badges & Drawer      |  | - Raw Code View |  |
|  |  - Model Switcher   |  |  - Chat Composer & Prompts     |  | - Copy / Export |  |
|  +---------------------+  +--------------------------------+  +-----------------+  |
+------------------------------------------+----------------------------------------+
                                           | HTTP REST /api/v1
                                           v
+-----------------------------------------------------------------------------------+
|                                FastAPI Backend Application                        |
|  +-----------------------------------------------------------------------------+  |
|  | API Router: /sessions, /messages, /artifacts, /health, /readiness           |  |
|  +-----------------------------------------------------------------------------+  |
|  | Intent Router & Skill Engine: [ NORMAL_QA | SHIP30 | ARTIFACT ]             |  |
|  +-----------------------------------------------------------------------------+  |
|  | Hybrid RAG Engine:                                                          |  |
|  |  [Query] -> [Dense Embedding: MiniLM-L6-v2] -> [Qdrant Dense Top-20]        |  |
|  |         \-> [BM25 Lexical Search]            -> [BM25 Lexical Top-20]        |  |
|  |                                                         |                   |  |
|  |         [Reciprocal Rank Fusion (k=60)] <---------------+                   |  |
|  |                     |                                                       |  |
|  |         [Cross-Encoder Reranker: Top-5 Selected Context]                     |  |
|  +-----------------------------------------------------------------------------+  |
|  | LLM Provider Abstraction: [ Gemini (google-genai) | Ollama (/api/chat) ]    |  |
|  +-----------------------------------------------------------------------------+  |
|  | Artifact Security Engine: Bleach Sanitizer + CSP Injector                   |  |
+-----------------------------------+--------------------+--------------------------+
                                    |                    |
                                    v                    v
                   +-----------------------+    +-----------------------+
                   |  PostgreSQL Database  |    |  Qdrant Cloud Vector  |
                   |  - sessions           |    |  - lenny_transcripts  |
                   |  - messages           |    |  - 384-dim dense      |
                   |  - artifacts          |    |  - chunk payloads     |
                   |  - message_sources    |    |  - BM25 metadata      |
                   |  - ingestion_runs     |    +-----------------------+
                   +-----------------------+
```

---

## 4. Non-Functional Requirements
- **Security**: No secrets in browser; sanitized iframe; parameterized SQL; robust CORS; per-user rate limiting.
- **Reliability**: Graceful degradation when external services are unreachable; health checks; automatic key/provider failover.
- **Maintainability**: Strict Python type annotations; TypeScript strict mode; modular directory structure.
- **Portability**: Complete Docker Compose setup and reproducible local CLI workflows.

---

## 5. Week-One Client Handoff Plan (Days 1–5)

To guarantee immediate operational readiness for enterprise deployment, the following 5-day handoff roadmap provides zero-friction client adoption:

### Day 1: Infrastructure Provisioning & Environment Validation
- **Actions**: Deploy `docker-compose.yml` on client infrastructure or cloud VM (AWS ECS / GCP Cloud Run / local server).
- **Verification**: Run `python -m pytest backend/tests/` (75/75 passing). Execute `/api/v1/health` and `/api/v1/readiness` smoke tests.
- **Deliverables**: Verified `.env` configuration, healthy PostgreSQL container, healthy vector database connection.

### Day 2: Ingestion & Knowledge Base Customization
- **Actions**: Ingest client-specific transcript datasets or execute the baseline 303-episode Lenny podcast ingestion script (`python backend/scripts/ingest.py`).
- **Verification**: Inspect Qdrant collection statistics and verify BM25 vocabulary cache generation.
- **Deliverables**: Fully populated vector store with 38,856 indexed semantic chunks and BM25 index.

### Day 3: Security & Compliance Audit
- **Actions**: Review rate limiting parameters (`RATE_LIMIT_CHAT_PER_MINUTE`), verify sandbox isolation in artifact viewer, review CORS whitelists.
- **Verification**: Execute `test_rate_limiting.py` and `test_sanitizer.py` test suites.
- **Deliverables**: Signed-off security isolation posture with zero XSS risk and authenticated user quota enforcement.

### Day 4: User Onboarding & Skill Customization
- **Actions**: Conduct technical walkthrough with client PMs and engineers covering:
  - Grounded RAG with signal-based confidence scoring (`HIGH`, `MODERATE`, `LOW`, `INSUFFICIENT`).
  - Ship 30 for 30 atomic essay generator with deterministic word-count and structural validation.
  - Interactive HTML/CSS artifact generation and sandboxed inspection.
  - Real SSE streaming via Ollama and Gemini fallback.
- **Deliverables**: Client team equipped with query playbooks and prompt templates.

### Day 5: Operational Telemetry & Production Sign-off
- **Actions**: Configure production logging, review latency metrics across dense/BM25/cross-encoder stages, confirm automated database migration pipelines.
- **Deliverables**: Final production readiness report and handoff sign-off.

