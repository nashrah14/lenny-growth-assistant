#!/usr/bin/env sh
# ============================================================
# Docker Entrypoint — The Lenny Growth Assistant Backend
# 1. Waits for PostgreSQL (handled by depends_on healthcheck)
# 2. Runs Alembic database migrations
# 3. Starts Uvicorn
# ============================================================
set -e

echo "[entrypoint] Running Alembic database migrations..."
cd /app
python -m alembic -c backend/alembic.ini upgrade head

echo "[entrypoint] Migrations complete. Starting uvicorn..."
exec uvicorn backend.app.main:app \
    --host "${HOST:-0.0.0.0}" \
    --port "${PORT:-8000}" \
    --workers 1 \
    --log-level "${LOG_LEVEL:-info}"
