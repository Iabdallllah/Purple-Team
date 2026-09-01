FROM python:3.11-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1

WORKDIR /app

# system deps
RUN apt-get update && apt-get install -y --no-install-recommends curl libpq5 && rm -rf /var/lib/apt/lists/*

# python deps (context is repo root for prod, also works for apps/api)
COPY apps/api/requirements.txt ./requirements.txt
COPY apps/api/requirements-dev.txt* ./
RUN pip install --upgrade pip && pip install -r requirements.txt

# copy packages needed at runtime
COPY packages ./packages
COPY apps/api ./

# install local packages
RUN pip install -e ./packages/agents -e ./packages/sandbox 2>&1 | tail -5 || true

# non-root
RUN useradd -m appuser && chown -R appuser /app
USER appuser

EXPOSE 8001

HEALTHCHECK --interval=15s --timeout=5s --retries=5 CMD curl -f http://localhost:8001/health || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001", "--workers", "2"]
