# Career Intelligence Platform — Backend

FastAPI backend for the Career Intelligence Platform.

## Stack

- Python 3.12
- FastAPI 0.115
- SQLAlchemy 2.0 (async)
- PostgreSQL 16
- Redis 7
- Alembic migrations
- JWT authentication with Argon2id password hashing
- sentence-transformers for AI embeddings
- FAISS for vector similarity search

## Setup

Install dependencies with uv:

```bash
uv venv .venv
uv sync
```

Copy environment file:

```bash
cp .env.example .env
```

Run database migrations:

```bash
uv run alembic upgrade head
```

Start development server:

```bash
uv run uvicorn src.main:app --reload --port 8000
```

API docs available at http://localhost:8000/docs

## Project Structure

```
src/
├── api/          # FastAPI routers and dependencies
├── core/         # Config, logging, security
├── db/           # Models, repositories, migrations
├── schemas/      # Pydantic request/response schemas
├── services/     # Business logic layer
├── ai/           # ML engines and embeddings
└── workers/      # Background job handlers
```

## Running Tests

```bash
uv run pytest
```
