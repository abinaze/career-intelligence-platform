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

This starts PostgreSQL 16 on port 5432 and Redis 7 on port 6379.

### Run Migrations

```bash
make migrate
```

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

## HuggingFace Spaces Deployment for Backend

HuggingFace Spaces supports FastAPI via the Docker SDK.

### Steps

Go to https://huggingface.co/spaces and create a new Space.

Select Docker SDK as the SDK type.

Set hardware to CPU Basic which is the free tier.

Push the backend code to the Space repository.

### Required Files in Space Root

The Space needs a Dockerfile, pyproject.toml, and the src directory.

### Environment Variables

Set these in Space Settings under Repository secrets:

```
SECRET_KEY=your-production-secret
DATABASE_URL=your-postgres-connection-url
REDIS_URL=your-redis-connection-url
ENVIRONMENT=production
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

```bash
docker compose -f infrastructure/docker/docker-compose.prod.yml up -d
```

## Environment Variables Reference

### Backend Variables

SECRET_KEY is required and has no default. It is the JWT signing secret.

DATABASE_URL is required and has no default. It is the PostgreSQL connection URL.

REDIS_URL is required and has no default. It is the Redis connection URL.

ENVIRONMENT is optional and defaults to development.

LOG_LEVEL is optional and defaults to INFO.

### Frontend Variables

NEXT_PUBLIC_API_URL is required. It defaults to http://localhost:8000 in development.

NEXT_PUBLIC_APP_URL is required. It defaults to http://localhost:3000 in development.
