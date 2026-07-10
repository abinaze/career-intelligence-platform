# Deployment Guide

## Local Development

### Prerequisites

Install Docker Desktop, Node.js 20 or higher, pnpm 9 or higher, Python 3.12 or higher, and uv.

Install uv with:

```bash
pip install uv
```

### Start Infrastructure

```bash
make dev-up
```

This starts PostgreSQL 16 on port 5432 and Redis 7 on port 6379 only. Run the backend and frontend directly on your host for the fastest local dev loop (hot reload, no rebuild on save).

### Run Migrations

```bash
make migrate
```

### Load Career Data

```bash
make load-onet
```

Seeds the `careers` table with O*NET occupations and builds the FAISS similarity index. Required before `/careers/recommendations` returns results.

### Start Backend

```bash
cd apps/backend
uv run uvicorn src.main:app --reload --port 8000
```

### Start Frontend

```bash
cd apps/frontend
pnpm dev
```

Frontend runs at http://localhost:3000

Backend runs at http://localhost:8000

API docs at http://localhost:8000/docs

## Full Docker Stack (all services containerised)

To run everything — Postgres, Redis, backend, and frontend — in containers:

```bash
make docker-build
make docker-up
```

This uses the `full` Docker Compose profile, which adds `backend` and `frontend` services on top of the base `postgres` + `redis` services. Source directories are bind-mounted so code changes are picked up without rebuilding.

```bash
make docker-logs   # tail all container logs
make docker-down   # stop everything
```

## Environment Variables Reference

### Backend Variables

`SECRET_KEY` is required and has no default. It is the JWT signing secret.

`DATABASE_URL` is required and has no default. It is the PostgreSQL connection URL.

`REDIS_URL` is required and has no default. It is the Redis connection URL.

`ENVIRONMENT` is optional and defaults to development.

`LOG_LEVEL` is optional and defaults to INFO.

`ANTHROPIC_API_KEY` is optional. Required only to enable the AI career chat feature (`POST /api/v1/chat/message`). Without it, the rest of the platform works normally and the chat endpoint returns `503`. Get a key at https://console.anthropic.com — see `apps/backend/.env.example`.

### Frontend Variables

`NEXT_PUBLIC_API_URL` is required. It defaults to http://localhost:8000 in development.

`NEXT_PUBLIC_APP_URL` is required. It defaults to http://localhost:3000 in development.

## HuggingFace Spaces Deployment for Backend

HuggingFace Spaces supports FastAPI via the Docker SDK.

### Steps

Go to https://huggingface.co/spaces and create a new Space.

Select Docker SDK as the SDK type.

Set hardware to CPU Basic which is the free tier.

Push the backend code to the Space repository, using `infrastructure/docker/Dockerfile.backend` (production target) as the Space Dockerfile.

### Required Files in Space Root

The Space needs a Dockerfile, pyproject.toml, and the src directory.

### Environment Variables

Set these in Space Settings under Repository secrets:

```
SECRET_KEY=your-production-secret
DATABASE_URL=your-postgres-connection-url
REDIS_URL=your-redis-connection-url
ENVIRONMENT=production
ANTHROPIC_API_KEY=your-anthropic-key   # optional, enables chat
```

### Free Database Options

Supabase free tier provides PostgreSQL.

Railway free tier provides PostgreSQL and Redis.

Render free tier provides PostgreSQL.

## Vercel Deployment for Frontend

Connect your GitHub repository to Vercel.

Set the root directory to apps/frontend.

Set the framework preset to Next.js.

Add these environment variables:

```
NEXT_PUBLIC_API_URL=https://your-hf-space.hf.space
NEXT_PUBLIC_APP_URL=https://your-app.vercel.app
```

## Self-Hosted Docker Deployment

A production compose file is not yet included in this repository. To self-host with Docker:

1. Build production images directly from the multi-stage Dockerfiles:

```bash
docker build -f infrastructure/docker/Dockerfile.backend --target production -t cip-backend:prod .
docker build -f infrastructure/docker/Dockerfile.frontend --target production -t cip-frontend:prod .
```

2. Run them alongside managed or self-hosted Postgres and Redis, passing the environment variables listed above.

3. Put `infrastructure/nginx/nginx.conf` in front of both services as a reverse proxy — it routes `/api/*` to the backend and everything else to the frontend, with gzip and rate limiting pre-configured.

A dedicated `docker-compose.prod.yml` tying all of this together is tracked for a future release.
