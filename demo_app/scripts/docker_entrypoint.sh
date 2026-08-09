#!/usr/bin/env bash
set -euo pipefail

: "${ANALYTICS_DB_PATH:=/data/schemaforms_analytics.db}"

# Optional feature flags (safe defaults).
: "${IP_GEO_ENABLED:=0}"
: "${IP_GEO_WORKER_ENABLED:=0}"
: "${IP_GEO_RATE_LIMIT_PER_MIN:=40}"

export ANALYTICS_DB_PATH IP_GEO_ENABLED IP_GEO_WORKER_ENABLED IP_GEO_RATE_LIMIT_PER_MIN

# Run migrations against the *mounted* SQLite DB.
python -m alembic -c alembic.ini upgrade head

HOST="${UVICORN_HOST:-0.0.0.0}"
PORT="${UVICORN_PORT:-5000}"
WORKERS="${UVICORN_WORKERS:-4}"
LOG_LEVEL="${UVICORN_LOG_LEVEL:-info}"

exec uvicorn src.main:app \
  --host "$HOST" \
  --port "$PORT" \
  --workers "$WORKERS" \
  --log-level "$LOG_LEVEL"
