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

### POST /assessments/sessions

Start a new assessment session.

### GET /assessments/sessions/{session_id}

Get the current state of an assessment session.

### POST /assessments/sessions/{session_id}/responses

Submit responses for a session.

### POST /assessments/sessions/{session_id}/complete

Mark a session as complete and trigger scoring.

## Career Endpoints

### GET /careers

List career paths with optional filters.

### GET /careers/{career_id}

Get details for a single career path.

### GET /careers/recommendations

Get personalized career recommendations for the authenticated user.

## Error Response Format

All errors return this structure:

```json
{
  "detail": "Human readable error message",
  "code": "MACHINE_READABLE_CODE"
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
