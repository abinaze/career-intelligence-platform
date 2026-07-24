#!/bin/sh
# Production entrypoint: run pending Alembic migrations, then start uvicorn.
#
# `alembic upgrade head` is idempotent — safe to run on every container
# start, not just the first deploy. This matters for single-container
# deployment targets (Hugging Face Spaces, Render, etc.) where there's no
# separate "run once" job step; the alternative — documenting "remember
# to run migrations manually after every schema change" — is exactly the
# kind of manual step that gets forgotten.
#
# Lives here (apps/backend/), not infrastructure/docker/, because the
# Dockerfile's build context is apps/backend — see docker-compose.dev.yml
# and docs/deployment/guide.md for why.
set -e

echo "Running database migrations..."
alembic upgrade head

echo "Starting server..."
exec uvicorn src.main:app \
    --host 0.0.0.0 \
    --port "${PORT:-8000}" \
    --workers "${UVICORN_WORKERS:-2}" \
    --no-access-log
