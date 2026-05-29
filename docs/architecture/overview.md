# System Architecture Overview

## High Level Diagram

```text
User Browser
     |
     | HTTPS / REST
     v
API Gateway Layer (FastAPI /api/v1/)
Rate limiting, CORS, JWT validation, Logging
     |
     |--------------------|--------------------|
     v                    v                    v
Auth Service         Profile Service     Recommendation Engine
     |                    |                    |
     v                    v                    v
                    PostgreSQL 16
     users, profiles, assessments, career_paths, recommendations
                          |
               |----------------------|
               v                      v
          Redis Cache           FAISS Vector Store
     Sessions, Rate limits       Career embeddings
```

## Service Responsibilities

### Authentication Service

Handles JWT issuance and validation using HS256.
Manages refresh token rotation.
Enforces role-based access control.

### Profile Service

Stores user biographical data.
Manages user preferences.
Computes profile completeness scoring.

### Psychometric Engine

Scores multi-dimensional traits using Big Five and extensions.
Assesses cognitive style.
Scores learning preferences.

### Recommendation Engine

Performs career vector similarity search using FAISS.
Applies multi-factor weighted ranking.
Calculates confidence scores.
Decomposes recommendations for explainability.

### Career Ontology Service

Integrates O*NET taxonomy.
Integrates ESCO taxonomy.
Enriches data with labor market signals.

## Recommendation Data Flow

Step 1. User completes psychometric assessment.

Step 2. Psychometric Engine scores traits into normalized vectors.

Step 3. Profile embedding is generated via sentence-transformers.

Step 4. FAISS similarity search runs against the career embedding index.

Step 5. Multi-factor re-ranking is applied.

Step 6. Explainability engine decomposes each recommendation.

Step 7. Confidence score is calculated per recommendation.

Step 8. Results are cached in Redis with a TTL of one hour.

## Security Architecture

Passwords are hashed with Argon2id.

JWT tokens are signed with HS256.

Rate limiting is applied per IP and per user.

CORS is restricted to known origins.

SQL injection is prevented via SQLAlchemy parameterized queries.

XSS is prevented via Content-Security-Policy headers.
