# Career Intelligence Platform

> An enterprise-grade, AI-powered career guidance system built entirely on free and open-source technology.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/Python-3.12+-blue.svg)](https://www.python.org/)
[![Next.js](https://img.shields.io/badge/Next.js-15-black.svg)](https://nextjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688.svg)](https://fastapi.tiangolo.com/)

## What This Is

The Career Intelligence Platform is not a recommendation website. It is a full behavioral intelligence and psychometric analysis system that:

- **Deeply profiles** personality, cognition, habits, learning style, and emotional tendencies
- **Scores behavioral patterns** using multi-factor psychometric engines
- **Recommends career paths** with explainable confidence scores
- **Evolves continuously** with each user interaction
- **Runs entirely free** — no paid APIs, no cloud lock-in

---

## Architecture Overview

```text
career-intelligence-platform/
├── apps/
│   ├── frontend/          # Next.js 15 + TypeScript + TailwindCSS
│   └── backend/           # FastAPI + Python 3.12 + PostgreSQL
├── packages/
│   ├── shared-types/      # Shared TypeScript type contracts
│   ├── eslint-config/     # Shared ESLint configuration
│   └── tsconfig/          # Shared TypeScript configuration
├── infrastructure/
│   ├── docker/            # Docker Compose configurations
│   ├── nginx/             # Reverse proxy configuration
│   └── scripts/           # Infrastructure automation
├── docs/
│   ├── architecture/      # System design documents
│   ├── api/               # API documentation
│   └── deployment/        # Deployment guides
└── .github/
    └── workflows/         # GitHub Actions CI/CD
Quick Start
Prerequisites
Node.js >= 20
pnpm >= 9
Python >= 3.12
uv
Docker + Docker Compose
Setup
git clone https://github.com/YOUR_USERNAME/career-intelligence-platform.git
cd career-intelligence-platform

make setup
make dev-up
make migrate
make load-onet
Development
# Terminal 1 — Frontend
cd apps/frontend && pnpm dev

# Terminal 2 — Backend
cd apps/backend && uv run uvicorn src.main:app --reload --port 8000
Frontend: http://localhost:3000
Backend API: http://localhost:8000
API Docs: http://localhost:8000/docs
Technology Stack
Layer	Technology
Frontend	Next.js 15, TypeScript, TailwindCSS, Shadcn UI, Framer Motion
State	Zustand, TanStack Query
Backend	FastAPI, Python 3.12, Pydantic v2
Database	PostgreSQL 16, SQLAlchemy 2.0, Alembic
Cache	Redis 7
AI/ML	sentence-transformers, scikit-learn, FAISS
Auth	JWT (HS256), RBAC
DevOps	Docker, GitHub Actions, uv, pnpm, Turbo
AI/ML Architecture
Psychometric Engine: Multi-dimensional personality and cognitive scoring
Behavioral Analysis: Pattern recognition from user task interactions
Embedding Layer: sentence-transformers/all-MiniLM-L6-v2
Career Compatibility: Multi-factor weighted ranking with FAISS
Explainability: Factor decomposition for every recommendation
Career Ontology: O*NET + ESCO taxonomy integration
License

MIT
