# HF Spaces - Purple Team API (Docker SDK)
# HF expects port 7860 and runs as user 1000
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1 \
    APP_ENV=production \
    DATABASE_URL=sqlite+aiosqlite:///./purple_hf.db \
    DATABASE_URL_SYNC=sqlite:///./purple_hf.db \
    REDIS_URL=memory:// \
    CHROMADB_URL=http://localhost:8000 \
    OLLAMA_URL=http://localhost:11434 \
    JWT_SECRET=hf-spaces-demo-secret-32-chars-minimum-please-change \
    PORT=7860

WORKDIR /app

# system deps for HF (curl for healthcheck)
RUN apt-get update && apt-get install -y --no-install-recommends curl libpq5 && rm -rf /var/lib/apt/lists/*

# install python deps (use HF cache)
COPY apps/api/requirements.txt ./requirements.txt
RUN pip install --upgrade pip && pip install -r requirements.txt && pip install aiosqlite email-validator python-socketio prometheus-fastapi-instrumentator

# copy packages needed at runtime (agents, sandbox, shared built is not needed for API)
COPY packages ./packages
COPY apps/api ./

# install local packages (no heavy deps like torch for HF demo - stub fallback will handle)
RUN pip install -e ./packages/agents -e ./packages/sandbox 2>&1 | tail -5 || true

# HF runs as 1000, create data dir
RUN mkdir -p /app/data && chown -R 1000:1000 /app
USER 1000

EXPOSE 7860

HEALTHCHECK --interval=15s --timeout=5s --retries=5 CMD curl -f http://localhost:7860/health || exit 1

# HF Spaces expects 7860, but our app defaults to 8001 - override via PORT env
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-7860} --workers 1"]
