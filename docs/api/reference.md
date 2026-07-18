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

## Stateless Endpoints (BYOS)

These endpoints back the local-device and bring-your-own-storage frontend
flows (see [`docs/architecture/byos.md`](../architecture/byos.md)). All
require authentication, but none read or write personal profile or
assessment data to the database — only the shared career catalog is read.
Callers supply their own data directly in the request and receive a
computed result back.

### GET /stateless/questions

Returns the static assessment question bank without creating a database
session, unlike `POST /assessment/start`.

Query parameters:

- `assessment_type` (string, default `"full"`) — `"full"` or `"quick"`.

Response 200:

```json
{
  "questions": [
    { "id": "ocean_open_01", "dimension": "openness", "prompt": "...", "reverse_scored": false }
  ],
  "total_questions": 38
}
```

### POST /stateless/score

Score a set of Likert responses without persisting anything.

Request body:

```json
{
  "responses": { "ocean_open_01": 4, "ocean_open_02": 3 }
}
```

Response 200:

```json
{
  "model_version": "1.0.0",
  "dimension_scores": [
    {
      "dimension": "openness",
      "display_name": "Openness",
      "score": 62.5,
      "confidence": 1.0,
      "item_count": 4,
      "low_label": "...",
      "high_label": "..."
    }
  ]
}
```

### POST /stateless/recommendations

Generate recommendations from client-supplied psychometric scores and
profile fields, rather than looking them up from the database. Uses the
same recommendation pipeline as `GET /careers/recommendations` — same
FAISS search, same multi-factor ranking, same explainability output.

Request body:

```json
{
  "dimension_scores": { "openness": 84.0, "investigative": 88.0 },
  "profile": {
    "education_level": "Bachelor's degree",
    "current_field": "Technology",
    "primary_goal": "Become a senior engineer"
  },
  "top_k": 10
}
```

Response 200: identical shape to `GET /careers/recommendations` — see
above.

## Storage — Google Drive (BYOS)

Backend broker for the Google Drive BYOS storage option (see
[`docs/architecture/byos.md`](../architecture/byos.md)). The backend never
persists the tokens these endpoints hand back — it only brokers the OAuth
handshake because the Google client secret can't live in browser JS. All
endpoints below require authentication except the callback, which is a
plain browser redirect target and carries no Authorization header.

### GET /storage/google-drive/connect

Starts a connect flow. Stages a short-lived ticket (5 min TTL) binding the
attempt to the current user, and returns the URL to send the browser to.

Response 200:

```json
{ "authorize_url": "https://accounts.google.com/o/oauth2/v2/auth?..." }
```

### GET /storage/google-drive/callback

Not called by the frontend directly — this is Google's redirect target.
Exchanges the authorization code for tokens, stages them under a
single-use exchange code (60s TTL), and 302-redirects the browser to
`{FRONTEND_URL}/settings?tab=storage&gdrive_exchange={code}` on success, or
`...&gdrive_error={reason}` on failure. Excluded from the OpenAPI schema
since it's not meant to be called as an API.

### POST /storage/google-drive/exchange

Claims a staged exchange code. Single-use — the code is deleted the moment
it's claimed, and claiming it twice returns 400 on the second call.

Request body:

```json
{ "exchange_code": "abc123..." }
```

Response 200:

```json
{
  "access_token": "ya29...",
  "refresh_token": "1//...",
  "token_type": "Bearer",
  "expires_at": "2026-07-16T21:00:00+00:00",
  "scope": "https://www.googleapis.com/auth/drive.appdata"
}
```

The frontend stores these client-side (IndexedDB, alongside local-device
data) and calls the Drive REST API directly from then on.

### POST /storage/google-drive/refresh

Exchanges a refresh token for a new access token when the current one
expires.

Request body:

```json
{ "refresh_token": "1//..." }
```

Response 200: same shape as `/exchange` (`refresh_token` is often omitted —
Google only rotates it occasionally).

### POST /storage/google-drive/disconnect

Revokes a token at Google. Idempotent: a token Google already considers
invalid still counts as revoked. The frontend clears its local copy
regardless of this call's outcome.

Request body:

```json
{ "token": "ya29..." }
```

Response 200:

```json
{ "revoked": true }
```

## Storage — OneDrive (BYOS)

Backend broker for the OneDrive BYOS storage option — same design as the
Google Drive section above, with one real difference: **there is no
`/disconnect` endpoint.** Microsoft's v2.0 endpoint has no simple
per-token revoke API for this flow, so disconnecting is handled entirely
client-side (the frontend clears its stored tokens and stops calling the
Graph API). See [`docs/architecture/byos.md`](../architecture/byos.md).

### GET /storage/onedrive/connect

Response 200:

```json
{ "authorize_url": "https://login.microsoftonline.com/common/oauth2/v2.0/authorize?..." }
```

### GET /storage/onedrive/callback

Microsoft's redirect target, not called by the frontend directly.
302-redirects to `{FRONTEND_URL}/settings?tab=storage&onedrive_exchange={code}`
on success, or `...&onedrive_error={reason}` on failure. Excluded from the
OpenAPI schema.

### POST /storage/onedrive/exchange

Request body:

```json
{ "exchange_code": "abc123..." }
```

Response 200:

```json
{
  "access_token": "EwB...",
  "refresh_token": "M.C...",
  "token_type": "Bearer",
  "expires_at": "2026-07-16T21:00:00+00:00",
  "scope": "Files.ReadWrite.AppFolder offline_access"
}
```

### POST /storage/onedrive/refresh

Request body:

```json
{ "refresh_token": "M.C..." }
```

Response 200: same shape as `/exchange`. Unlike Google, Microsoft always
rotates the refresh token on use, so `refresh_token` is reliably present
here (not just "sometimes," as noted for Google Drive above).

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
