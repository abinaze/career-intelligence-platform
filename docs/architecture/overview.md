# System Architecture Overview

## System Boundaries

```text
┌─────────────────────────────────────────────────────┐
│                   User Browser                      │
│              Next.js Frontend (SSR)                 │
└───────────────────────┬─────────────────────────────┘
                        │ HTTPS / REST
┌───────────────────────▼─────────────────────────────┐
│                  API Gateway Layer                  │
│           FastAPI (versioned /api/v1/)              │
│     Rate limiting · CORS · JWT · Logging            │
└──────┬──────────┬──────────┬────────────────────────┘
       │          │          │
┌──────▼───┐ ┌────▼────┐ ┌───▼──────────────┐
│   Auth   │ │ Profile │ │ Recommendation   │
│  Service │ │ Service │ │     Engine       │
└──────┬───┘ └────┬────┘ └──────────────────┘
       │           │
┌──────▼───────────▼────────────────────────┐
│              PostgreSQL 16                │
│ users · profiles · assessments            │
│ career_paths · recommendations            │
└───────────────────────────────────────────┘
                        │
┌───────────────────────▼──────────────┐
│             Redis Cache              │
│          Sessions · Jobs             │
└──────────────────────────────────────┘

┌──────────────────────────────────────┐
│          FAISS Vector Store          │
│         Career embeddings            │
└──────────────────────────────────────┘
Service Responsibilities
Authentication Service
JWT issuance and validation (HS256)
Refresh token rotation
RBAC enforcement
Profile Service
User biographical data
Preference management
Profile completeness scoring
Psychometric Engine
Multi-dimensional trait scoring (Big Five + extensions)
Cognitive style assessment
Learning preference scoring
Recommendation Engine
Career vector similarity search (FAISS)
Multi-factor weighted ranking
Confidence score calculation
Explainability decomposition
Career Ontology Service
O*NET taxonomy integration
ESCO taxonomy integration
Labor market signal enrichment
Data Flow: Recommendation Generation
User completes psychometric assessment
Psychometric Engine scores traits into normalized vectors
Profile embedding generated via sentence-transformers
FAISS similarity search against career embedding index
Multi-factor re-ranking applied
Explainability engine decomposes each recommendation
Confidence score calculated per recommendation
Results cached in Redis (TTL: 1 hour)
Security Architecture
Passwords hashed with Argon2id
JWT signed with HS256
Rate limiting per IP and per user
CORS restricted to known origins
SQL injection prevention via SQLAlchemy parameterized queries
XSS prevention via Content-Security-Policy headers
