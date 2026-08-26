# Backend Dockerfile — The Lenny Growth Assistant
FROM python:3.11-slim

WORKDIR /app

# Install system build dependencies (curl needed for compose healthcheck)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY backend/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code
COPY backend/ /app/backend/
COPY data/ /app/data/
COPY lennys-podcast-transcripts-main/ /app/lennys-podcast-transcripts-main/

# Make entrypoint executable
RUN chmod +x /app/backend/entrypoint.sh

ENV PYTHONPATH=/app
ENV PORT=8000
ENV HOST=0.0.0.0

EXPOSE 8000

# entrypoint.sh runs Alembic migrations then starts uvicorn
ENTRYPOINT ["/app/backend/entrypoint.sh"]
