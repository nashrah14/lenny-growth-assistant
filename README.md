# The Lenny Growth Assistant

> **Production-Grade Grounded RAG Platform, Ship 30 Content Engine, In-App Sandboxed Artifact Workspace, and Secure Authentication System powered by 300+ Lenny's Podcast Transcripts.**

---

## 🌟 Executive Summary & Product Overview

**The Lenny Growth Assistant** is a full-stack, enterprise-grade AI assistant engineered to transform **300+ episodes of Lenny's Podcast** (~4.6M words of world-class product, growth, and leadership wisdom) into instant, strictly grounded answers, Ship 30 for 30 atomic essays, and live interactive HTML/Markdown artifacts.

Built for Product Managers, Growth Leaders, and Founders, the platform combines:
- **Enterprise Authentication (OWASP Compliant)**: Secure user registration and login with **Argon2id** password hashing, signed JWT session management, and **HttpOnly; SameSite=Lax** session cookies (immune to XSS token theft).
- **Strict User-Level Data Isolation**: Complete relational multi-tenancy in PostgreSQL where every session, message, and artifact is strictly owned and accessible only by its authenticated creator.
- **Two-Stage Hybrid RAG**: Parallel Dense Semantic Search (`sentence-transformers/all-MiniLM-L6-v2`, 384d) + BM25 Lexical Matching fused via **Reciprocal Rank Fusion (RRF, $k=60$)** and refined by a **Cross-Encoder Reranker** (`cross-encoder/ms-marco-MiniLM-L-6-v2`).
- **Strict Grounding & Zero Hallucination**: 100% of factual answers cite verified episode titles, speakers, timestamps, and seekable YouTube links with deterministic "no-evidence" fallback.
- **Ship 30 for 30 Writing Skill**: Generates high-impact, skimmable ~1,250-word atomic essays featuring punchy hooks, 3–5 bolded framework pillars, tactical steps, and closing takeaways.
- **In-App Sandboxed Artifact Viewer**: Renders interactive calculators, growth models, dashboards, and strategy documents in a split-screen panel with defense-in-depth XSS sanitization (`bleach` + `iframe sandbox="allow-scripts"` + strict CSP).
- **Dual-Store Architecture**: Transactional ACID state in **PostgreSQL 16** (with Alembic migrations) paired with high-dimensional vector search in **Qdrant Cloud**.
- **Model Abstraction & Dynamic Switching**: Seamless runtime toggling between cloud LLMs (**Google Gemini 3.6 Flash** via the official `google-genai` SDK) and local/remote **Ollama** models.

---

## 🏗️ Target Architecture

```
                    React 18 + TypeScript UI
                      | (HTTP REST /api/v1 + HttpOnly Cookie)
                      v
                   FastAPI 0.115+
                      |
           Authentication Dependency & Intent Router
                      |
        +-------------+-------------+
        |             |             |
        v             v             v
    Normal QA      Ship 30       Artifact
    (RAG Skill)  (Essay Skill) (HTML/CSS & MD)
        |             |             |
        +-------------+-------------+
                      |
                      v
             Hybrid RAG Pipeline
                      |
        +-------------+-------------+
        |                           |
        v                           v
   Dense Search (Qdrant)       BM25 Lexical Index
   (all-MiniLM-L6-v2, 384d)    (Tokenized Inverted Index)
        |                           |
        +-------------+-------------+
                      |
                      v
          Reciprocal Rank Fusion (k=60)
                      |
                      v
          Cross-Encoder Reranker (Top-5)
                      |
                      v
              LLM Router Layer
             /                \
        Google Gemini       Remote Ollama
        (gemini-3.6-flash)  (/api/chat)
```

---

## 🚀 Quick Start & Prerequisites

### 1. Prerequisites
- **Python**: 3.11+ (Tested on Python 3.11, 3.12, 3.13)
- **Node.js**: 20+ (with npm 10+)
- **PostgreSQL**: Local service on port 5432
- **Google Gemini API Key** (configured in `.env`)

---

### 2. Environment Configuration

```ini
# Application
APP_NAME="The Lenny Growth Assistant"
APP_ENV=development
PORT=8000
FRONTEND_URL=http://localhost:5173

# PostgreSQL Database
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/lenny_assistant

# Authentication & Security
JWT_SECRET_KEY=lenny-secret-key-change-in-production-2026-secure-jwt
COOKIE_NAME=lenny_auth_session
COOKIE_SECURE=false

# Google Gemini API
LLM_PROVIDER=gemini
GEMINI_API_KEY=your_gemini_api_key
GEMINI_MODEL=gemini-3.6-flash

# Ollama Configuration
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2
```

---

### 3. Local Installation & Startup

#### Backend Setup
```bash
# 1. Install backend dependencies
cd backend
pip install -r requirements.txt

# 2. Initialize database schema (Creates users, sessions, messages, artifacts tables)
python -m backend.app.cli init-db

# 3. Start FastAPI dev server (port 8000)
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
```

#### Frontend Setup (in a new terminal)
```bash
# 1. Install frontend dependencies
cd frontend
npm install

# 2. Start Vite dev server (port 5173)
npm run dev
```

Open **`http://localhost:5173`** in your browser.

---

## 🧪 Automated Testing Suite

```bash
# 1. Run all backend tests (28 unit, integration, auth, and security tests)
python -m pytest backend/tests -v

# 2. Run frontend Vitest component tests (5 tests)
cd frontend && npx vitest run

# 3. Run frontend production build verification
cd frontend && npm run build
```

---

## 🛡️ Security Architecture

1. **Password Hashing (Argon2id)**: Memory-hard hashing using `argon2-cffi` configured with 64MB RAM cost and 3 iterations.
2. **HttpOnly Session Cookies**: Authentication tokens are signed JWTs delivered exclusively via `HttpOnly; SameSite=Lax` cookies, preventing JavaScript XSS token theft.
3. **User Isolation**: All session, message, and artifact endpoints strictly verify `user_id == current_user.id`. Cross-user access returns `404 Not Found`.
4. **Multi-Layer HTML Sanitization**: Generated HTML artifacts pass through `bleach` to strip malicious tags (`<script>`, `<object>`, `<embed>`, `<iframe>`) and inline event handlers (`onclick`, `onerror`).
5. **Sandboxed Iframe Isolation**: Artifacts render in an `<iframe>` with `sandbox="allow-scripts"`, strictly omitting `allow-same-origin` and `allow-top-navigation`.
6. **Strict Content Security Policy (CSP)**: Injects `<meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; script-src 'unsafe-inline';">`.
7. **No Secret Logging**: Structured logger masks tokens, database passwords, and authorization headers.
