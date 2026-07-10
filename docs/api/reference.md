# API Reference

Base URL: http://localhost:8000/api/v1

Interactive docs: http://localhost:8000/docs

## Authentication

All protected endpoints require an Authorization header in this format:

```
Authorization: Bearer your_access_token_here
```

## Auth Endpoints

### POST /auth/register

Register a new user account.

Request body:

```json
{
  "email": "user@example.com",
  "password": "StrongPass123",
  "full_name": "Jane Doe"
}
```

Response 201:

```json
{
  "user": {
    "id": "uuid",
    "email": "user@example.com",
    "full_name": "Jane Doe",
    "role": "user",
    "is_verified": false
  },
  "tokens": {
    "access_token": "eyJ...",
    "refresh_token": "eyJ...",
    "token_type": "bearer",
    "expires_in": 1800
  }
}
```

### POST /auth/token

Login with email and password using OAuth2 form format.

Request is multipart/form-data with fields username and password.

Response 200:

```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

### POST /auth/refresh

Rotate refresh token and issue a new access token.

Request body:

```json
{
  "refresh_token": "eyJ..."
}
```

### POST /auth/logout

Revoke the provided refresh token.

Request body:

```json
{
  "refresh_token": "eyJ..."
}
```

Response is 204 No Content.

### GET /auth/me

Get the current authenticated user.

Response 200:

```json
{
  "id": "uuid",
  "email": "user@example.com",
  "full_name": "Jane Doe",
  "role": "user",
  "is_verified": false,
  "is_active": true
}
```

## Assessment Endpoints

### POST /assessment/start

Start a new psychometric assessment session. Returns the session and the full question list.

Response 200:

```json
{
  "session": {
    "id": "uuid",
    "user_id": "uuid",
    "assessment_type": "big_five_riasec",
    "status": "in_progress",
    "started_at": "2026-07-10T12:00:00Z",
    "completed_at": null
  },
  "questions": [
    {
      "id": "q1",
      "text": "I enjoy exploring abstract ideas.",
      "dimension": "openness",
      "reversed": false,
      "options": [
        { "value": 1, "label": "Strongly Disagree" },
        { "value": 5, "label": "Strongly Agree" }
      ]
    }
  ],
  "total_questions": 40
}
```

### POST /assessment/submit

Submit all responses for a session and receive scored results.

Request body:

```json
{
  "session_id": "uuid",
  "responses": {
    "q1": 4,
    "q2": 3
  }
}
```

Response 200:

```json
{
  "session": { "...": "..." },
  "results": {
    "session_id": "uuid",
    "assessment_type": "big_five_riasec",
    "completed_at": "2026-07-10T12:10:00Z",
    "dimension_scores": [
      {
        "dimension": "openness",
        "display_name": "Openness",
        "score": 84.0,
        "confidence": 0.91,
        "percentile": null
      }
    ],
    "model_version": "1.0.0"
  }
}
```

### GET /assessment/results/{session_id}

Get results for a completed session.

## Profile Endpoints

### GET /profile

Get or auto-create the authenticated user's career profile.

Response 200:

```json
{
  "id": "uuid",
  "user_id": "uuid",
  "age_range": "25-34",
  "education_level": "Bachelor's degree",
  "current_field": "Technology",
  "years_of_experience": 5,
  "country": "India",
  "primary_goal": "Become a senior software engineer",
  "career_concerns": ["work-life balance"],
  "desired_work_environment": "Remote",
  "onboarding_completed": true,
  "onboarding_step": 4,
  "completeness_score": 85.0
}
```

### PATCH /profile

Partially update profile fields. Omitted fields are unchanged. Recomputes `completeness_score` automatically.

Request body (all fields optional):

```json
{
  "education_level": "Master's degree",
  "years_of_experience": 6
}
```

Response 200: same shape as `GET /profile`.

## Career Endpoints

### GET /careers/recommendations

Get personalised career recommendations for the authenticated user, ranked by composite score.

Requires a completed assessment — returns `400` if none exists, `404` if no profile exists.

Query parameters:

- `top_k` (integer, 1–50, default 10) — number of recommendations to return.

Response 200:

```json
{
  "user_id": "uuid",
  "profile_completeness": 85.0,
  "recommendations": [
    {
      "career_id": "uuid",
      "onet_code": "15-1252.00",
      "title": "Software Developers",
      "broad_category": "Computer and Mathematical",
      "description": "...",
      "median_salary_usd": 124200.0,
      "outlook_percentile": 88.0,
      "composite_score": 0.87,
      "similarity_score": 0.80,
      "riasec_score": 0.76,
      "explanation": {
        "career_id": "uuid",
        "onet_code": "15-1252.00",
        "title": "Software Developers",
        "summary": "Software Developers is a high-confidence match based on your Investigative and Openness orientation.",
        "confidence_band": "high",
        "factors": [
          {
            "factor": "semantic_match",
            "label": "Profile-career semantic similarity",
            "score": 0.80,
            "driver": "strong match",
            "detail": "Your overall profile aligns with Software Developers at 80% semantic similarity."
          }
        ],
        "top_matching_traits": ["Investigative", "Openness"]
      }
    }
  ],
  "warning": null
}
```

If the career database has not been seeded, `warning` explains how to fix it (`Run: make load-onet`) and `recommendations` is an empty array.

## Chat Endpoints

### POST /chat/message

Send a message to the AI career counsellor. The system prompt is automatically personalised using the user's psychometric scores and profile fields.

Requires `ANTHROPIC_API_KEY` to be configured on the backend — returns `503` if not set.

Request body:

```json
{
  "message": "What careers match my Investigative score?",
  "history": [
    { "role": "user", "content": "Hi" },
    { "role": "assistant", "content": "Hello! How can I help with your career today?" }
  ]
}
```

`history` is optional (max 20 prior turns, oldest first).

Response 200:

```json
{
  "reply": "Based on your strong Investigative score, careers like...",
  "model": "claude-sonnet-4-6",
  "tokens_used": 187
}
```

## Error Response Format

All errors return this structure:

```json
{
  "detail": "Human readable error message"
}
```

Status code meanings:

- 400 means bad request or validation error
- 401 means unauthenticated
- 403 means forbidden due to insufficient role
- 404 means resource not found
- 409 means conflict such as duplicate email
- 422 means unprocessable entity
- 429 means rate limit exceeded
- 500 means internal server error
- 502/504 mean the chat service (Anthropic API) failed or timed out
- 503 means the chat service is not configured (missing ANTHROPIC_API_KEY)
