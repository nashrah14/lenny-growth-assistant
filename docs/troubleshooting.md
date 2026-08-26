# Troubleshooting & Operations Guide

## The Lenny Growth Assistant

---

## 1. Common Issues & Diagnostics

### 1.1 Database Connection Errors (`ConnectionRefusedError` / `Password authentication failed`)
- **Symptom**: `sqlalchemy.exc.OperationalError: could not connect to server: Connection refused (0x0000274D/10061)`
- **Remedy**:
  1. Verify PostgreSQL service is running locally on port `5432` (`netstat -ano | findstr 5432` or Task Manager -> Services -> postgresql).
  2. Verify your `DATABASE_URL` format in `.env`: `postgresql+asyncpg://<user>:<password>@localhost:5432/lenny_assistant`.
  3. Ensure database `lenny_assistant` exists (`createdb -U postgres lenny_assistant` or via pgAdmin).
  4. If using SQLite for local testing without PostgreSQL, set: `DATABASE_URL=sqlite+aiosqlite:///./lenny_assistant.db`.

---

### 1.2 Qdrant Cloud Connection / Authentication Errors
- **Symptom**: `qdrant_client.http.exceptions.UnauthorizedException: Invalid api-key` or `Response status: 403`
- **Remedy**:
  1. Verify `QDRANT_URL` (e.g. `https://xyz.cloud.qdrant.io:6333`) and `QDRANT_API_KEY` are populated in `.env`.
  2. Check firewall or corporate proxy settings allowing HTTPS outbound traffic on port 6333 or 443.
  3. Test connectivity via health check: `GET http://localhost:8000/api/v1/health`.

---

### 1.3 Gemini API Key Issues (`google.genai.errors.APIError`)
- **Symptom**: `403 Forbidden` or `API key not valid`
- **Remedy**:
  1. Ensure `GEMINI_API_KEY` is set in `.env`.
  2. Ensure your key has permissions for Gemini 1.5 Flash (`gemini-1.5-flash` or `gemini-2.0-flash`).
  3. The backend uses the official `google-genai` SDK (`from google import genai`).

---

### 1.4 Remote Ollama Timeout or Connection Refused
- **Symptom**: `httpx.ConnectError: All connection attempts failed` or `ReadTimeoutException`
- **Remedy**:
  1. Confirm `OLLAMA_BASE_URL` in `.env` (e.g. `http://my-remote-ollama:11434`).
  2. Increase timeout if running large models: `OLLAMA_TIMEOUT_SECONDS=180`.
  3. Verify the model name specified in `OLLAMA_MODEL` is pulled on the Ollama host (`ollama list`).

---

### 1.5 Transcript Ingestion Speed & Memory
- **Symptom**: Ingestion of all 303 episodes taking a long time on CPU.
- **Remedy**:
  1. Use batching: the ingestion CLI batches embeddings in chunks of 64 (`--batch-size 64`).
  2. Run a partial dry-run or limit test: `python -m app.cli ingest --limit 10`.
  3. Run full rebuild when needed: `python -m app.cli ingest --rebuild`.
