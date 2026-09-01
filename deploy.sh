#!/usr/bin/env bash
set -euo pipefail

# Purple Platform - Production deploy
# Usage: ./deploy.sh [--with-monitoring] [--build] [--logs]

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
COMPOSE="docker compose -f docker-compose.prod.yml"
WITH_MONITORING=false
DO_BUILD=false

for arg in "$@"; do
  case "$arg" in
    --with-monitoring) WITH_MONITORING=true ;;
    --build) DO_BUILD=true ;;
    --logs) tail -f /tmp/api.log /tmp/web.log 2>/dev/null || docker compose -f docker-compose.prod.yml logs -f ;;
    --help) echo "Usage: $0 [--with-monitoring] [--build] [--logs]"; exit 0 ;;
  esac
done

if [ ! -f .env ]; then
  echo "No .env found - creating from .env.prod.example"
  cp .env.prod.example .env
  echo ">> Edit .env and set POSTGRES_PASSWORD and JWT_SECRET before continuing"
fi

# Validate JWT secret length
JWT_LEN=$(grep -E "^JWT_SECRET=" .env | cut -d= -f2 | wc -c)
if [ "$JWT_LEN" -lt 32 ]; then
  echo "WARNING: JWT_SECRET should be >=32 chars"
fi

echo "==> Pulling base images..."
$COMPOSE pull postgres redis chromadb ollama || true

if [ "$DO_BUILD" = true ]; then
  echo "==> Building api & web (this may take a few minutes)..."
  $COMPOSE build api web
else
  echo "==> Building api & web (cached)..."
  $COMPOSE build api web
fi

echo "==> Starting core stack..."
$COMPOSE up -d postgres redis chromadb ollama
echo "Waiting for postgres healthy..."
# Use compose ps to get correct container name (handles -1 suffix)
for i in 1 2 3 4 5 6 7 8 9 10; do
  CID=$($COMPOSE ps -q postgres 2>/dev/null | head -1)
  if [ -n "$CID" ] && docker inspect --format='{{.State.Health.Status}}' "$CID" 2>&1 | grep -q healthy; then
    echo "postgres healthy"
    break
  fi
  # also try direct name
  if docker inspect --format='{{.State.Health.Status}}' purple-postgres-1 2>&1 | grep -q healthy; then
    echo "postgres healthy"
    break
  fi
  if docker inspect --format='{{.State.Health.Status}}' purple-postgres 2>&1 | grep -q healthy; then
    echo "postgres healthy"
    break
  fi
  sleep 3
  echo "wait $i..."
done
# Also wait a bit for redis/chroma to start (no need to be healthy for migration)
sleep 5

echo "==> Running DB migrations..."
$COMPOSE run --rm api alembic upgrade head || echo "migration failed - check logs (may already be at head)"

echo "==> Starting api + worker + web..."
$COMPOSE up -d api worker web

if [ "$WITH_MONITORING" = true ]; then
  echo "==> Starting monitoring..."
  $COMPOSE --profile monitoring up -d prometheus grafana
fi

echo ""
echo "Done! Services:"
echo "  API:        http://localhost:8001/docs (health: http://localhost:8001/health)"
echo "  Web:        http://localhost:3000"
echo "  Grafana:    http://localhost:3002 (admin / from .env)"
echo "  Prometheus: http://localhost:9090"
echo "  Juice Shop: http://localhost:3001 (if targets profile: docker compose --profile targets up -d)"
echo ""
echo "Logs: docker compose -f docker-compose.prod.yml logs -f api web worker"
echo "Stop: docker compose -f docker-compose.prod.yml down"
