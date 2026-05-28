# API Reference

Base URL: `http://localhost:8000/api/v1`

Interactive docs: `http://localhost:8000/docs`

---

## Authentication

All protected endpoints require:

Authorization: `Bearer <access_token>`

---

# Auth Endpoints

## POST /auth/register

Register a new user account.

### Request

```json
{
  "email": "user@example.com",
  "password": "StrongPass123",
  "full_name": "Jane Doe"
}
Response — 201 Created
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
POST /auth/token

Login with email and password (OAuth2 form).

Request — multipart/form-data
username=user@example.com
password=StrongPass123
Response — 200 OK
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer",
  "expires_in": 1800
}
POST /auth/refresh

Rotate refresh token and issue new access token.

Request
{
  "refresh_token": "eyJ..."
}
POST /auth/logout

Revoke the provided refresh token.

Request
{
  "refresh_token": "eyJ..."
}
Response — 204 No Content
GET /auth/me

Get current authenticated user.

Response — 200 OK
{
  "id": "uuid",
  "email": "user@example.com",
  "full_name": "Jane Doe",
  "role": "user",
  "is_verified": false,
  "is_active": true
}
Assessment Endpoints
POST /assessments/sessions

Start a new assessment session.

GET /assessments/sessions/{session_id}

Get assessment session state.

POST /assessments/sessions/{session_id}/responses

Submit responses for a session.

POST /assessments/sessions/{session_id}/complete

Complete session and trigger scoring.

Career Endpoints
GET /careers

List career paths with filters.

GET /careers/{career_id}

Get single career path details.

GET /careers/recommendations

Get personalized recommendations for the authenticated user.

Error Responses

All errors follow this structure:

{
  "detail": "Human readable error message",
  "code": "MACHINE_READABLE_CODE"
}
Status	Meaning
400	Bad request / validation error
401	Unauthenticated
403	Forbidden (insufficient role)
404	Resource not found
409	Conflict (e.g. duplicate email)
422	Unprocessable entity
429	Rate limit exceeded
500	Internal server error

