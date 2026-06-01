# Career Intelligence Platform


An enterprise-grade, AI-powered career guidance system built entirely on free and open-source technology.

## What This Is

The Career Intelligence Platform is not a recommendation website. It is a full behavioral intelligence and psychometric analysis system that:

- Deeply profiles personality, cognition, habits, learning style, and emotional tendencies
- Scores behavioral patterns using multi-factor psychometric engines
- Recommends career paths with explainable confidence scores
- Evolves continuously with each user interaction
- Runs entirely free with no paid APIs and no cloud lock-in

## Repository Structure

```text
career-intelligence-platform/
├── apps/
│   ├── frontend/
│   └── backend/
├── packages/
│   ├── shared-types/
│   ├── eslint-config/
│   └── tsconfig/
├── infrastructure/
│   ├── docker/
│   ├── nginx/
│   └── scripts/
├── docs/
│   ├── architecture/
│   ├── api/
│   └── deployment/
└── .github/
    └── workflows/
```

## Prerequisites

- Node.js >= 20
- pnpm >= 9
- Python >= 3.12
- uv
- Docker and Docker Compose

## Quick Start

```bash
git clone https://github.com/YOUR_USERNAME/career-intelligence-platform.git
cd career-intelligence-platform
make setup
make dev-up
make migrate
make load-onet
```

## Running Locally

Start the frontend:

```bash
cd apps/frontend
pnpm dev
```

Start the backend:

```bash
cd apps/backend
uv run uvicorn src.main:app --reload --port 8000
```

Frontend runs at http://localhost:3000

Backend runs at http://localhost:8000

API docs at http://localhost:8000/docs

## Technology Stack

Frontend uses Next.js 15, TypeScript, TailwindCSS, Shadcn UI, and Framer Motion.

State management uses Zustand and TanStack Query.

Backend uses FastAPI, Python 3.12, and Pydantic v2.

Database uses PostgreSQL 16, SQLAlchemy 2.0, and Alembic.

Cache uses Redis 7.

AI and ML uses sentence-transformers, scikit-learn, and FAISS.

Auth uses JWT with HS256 and RBAC.

DevOps uses Docker, GitHub Actions, uv, pnpm, and Turbo.

## AI and ML Architecture

- Psychometric Engine for multi-dimensional personality and cognitive scoring
- Behavioral Analysis for pattern recognition from user task interactions
- Embedding Layer using sentence-transformers/all-MiniLM-L6-v2
- Career Compatibility using multi-factor weighted ranking with FAISS
- Explainability through factor decomposition for every recommendation
- Career Ontology using O*NET and ESCO taxonomy integration

## License

MIT
