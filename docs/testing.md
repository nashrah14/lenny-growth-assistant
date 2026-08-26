# Testing Strategy & Test Plan

## The Lenny Growth Assistant

---

## 1. Testing Philosophy & Test Pyramid

The application employs a robust 3-tier testing pyramid to guarantee deterministic grounding, fast CI/CD execution, and production resilience without requiring live cloud API billing during automated unit testing.

```
       / \
      / E2E \       -> End-to-end API & UI flows (FastAPI TestClient, React Testing Library)
     /-------\
    /  Integ  \     -> PostgreSQL DB CRUD, Alembic migrations, Qdrant adapter with mock
   /-----------\
  /    Unit     \   -> RRF fusion, Chunking, Bleach Sanitizer, Intent Routing, Prompts
 /---------------\
```

---

## 2. Automated Test Suites

### 2.1 Backend Unit & Integration Tests (`pytest`)
- **Location**: `backend/tests/`
- **Modules**:
  - `test_config.py`: Validates Pydantic settings parsing, defaults, and type coercions.
  - `test_chunking.py`: Tests text splitting, overlap boundaries, speaker tag preservation, and edge cases (empty text, single long utterance).
  - `test_fusion.py`: Tests Reciprocal Rank Fusion (RRF) math, rank normalization, tie-breaking, and empty input lists.
  - `test_reranker.py`: Tests cross-encoder scoring and graceful fallback to RRF when reranker model raises exceptions.
  - `test_sanitizer.py`: Tests artifact HTML sanitization, blocking `<script>`, `javascript:` URLs, inline `onload`/`onerror`, while allowing safe SVG, CSS, and layout markup.
  - `test_intent_router.py`: Tests deterministic intent classification (`NORMAL_QA`, `SHIP30`, `ARTIFACT`) against 20+ real user queries.
  - `test_ship30_skill.py`: Validates Ship 30 for 30 essay generation structure (word count, hook, headers, grounded claims).
  - `test_llm_router.py`: Tests provider abstraction, Gemini & Ollama adapters, timeouts, and error normalization.
  - `test_session_service.py`: Tests PostgreSQL session creation, message persistence, isolation between sessions, and history windowing.
  - `test_api_routes.py`: Tests FastAPI endpoints (`/sessions`, `/messages`, `/artifacts`, `/health`) with status codes, validation errors, and response models.

### 2.2 Frontend Unit & Component Tests (`vitest` + `@testing-library/react`)
- **Location**: `frontend/tests/`
- **Components**:
  - `ChatContainer.test.tsx`: Tests message rendering, source badges, and streaming indicators.
  - `ArtifactViewer.test.tsx`: Tests tab switching (Live Preview vs Raw Code), copy button, and sandboxed iframe attributes.
  - `Sidebar.test.tsx`: Tests session listing, active session highlighting, and New Chat trigger.
  - `ModelSwitcher.test.tsx`: Tests provider selection dropdown and state propagation.

---

## 3. Manual UI Test Plan (Evaluator Walkthrough)

| Step | Action | Expected Result |
| :--- | :--- | :--- |
| **1** | Open `http://localhost:5173` | App loads in dark mode; 4 quick-start prompts displayed; model toggle shows default provider. |
| **2** | Click quick prompt: *"How did Superhuman measure PMF?"* | Chat shows multi-stage progress; streams answer detailing Rahul Vohra's 40% rule; renders clickable source pill. |
| **3** | Click source pill | Drawer slides open showing Rahul Vohra episode, YouTube URL with timestamp, and matched transcript quote. |
| **4** | Send follow-up: *"Turn this into a Ship 30 essay."* | System routes to `SHIP30` skill; generates ~1,250-word structured atomic essay with hook, headings, and bold points. |
| **5** | Send message: *"Create an interactive CAC & LTV growth model calculator."* | System routes to `ARTIFACT` skill; renders live interactive calculator in right-hand Artifact Viewer panel. |
| **6** | Click "Raw Code" tab in Artifact Viewer | Displays formatted, syntax-highlighted HTML/JS code; clicking "Copy" copies code to clipboard. |
| **7** | Click "+ New Chat" in sidebar | Fresh conversation opens; previous session remains preserved in sidebar history. |
| **8** | Switch Model Provider to "Ollama" | Model badge updates; subsequent queries route to configured Ollama endpoint. |
| **9** | Ask out-of-domain question: *"What is dark matter?"* | Assistant safely responds with no-evidence disclaimer without hallucinating citations. |

---

## 4. Test Execution Commands

```bash
# Run backend test suite with coverage
cd backend
pytest -v --cov=app --cov-report=term-missing

# Run frontend tests
cd frontend
npm test -- --run
```
