# Security Policy

## Supported Versions

This project is under active development on the `main` branch. Security fixes
are applied to `main` only; there are no maintained release branches at this
stage.

| Branch | Supported |
|---|---|
| `main` | ✅ |

## Reporting a Vulnerability

**Please do not open a public GitHub issue for security vulnerabilities.**

If you discover a security vulnerability in this project — including but not
limited to authentication bypass, injection vulnerabilities, insecure direct
object references, or exposure of sensitive data — report it privately using
one of the following methods:

1. **Preferred:** Use GitHub's [private vulnerability reporting](https://github.com/abinaze/career-intelligence-platform/security/advisories/new)
   feature on this repository. This creates a private advisory visible only to
   maintainers until it is resolved.
2. Contact a maintainer directly through their GitHub profile if the advisory
   feature is unavailable to you.

### What to include

To help us triage and fix the issue quickly, please include:

- A description of the vulnerability and its potential impact
- Steps to reproduce it, including any proof-of-concept code
- The affected component (frontend, backend, a specific endpoint, etc.)
- Your assessment of severity, if you have one

### What to expect

- **Acknowledgement** within 5 business days.
- **Initial assessment** of severity and validity within 10 business days.
- **Fix timeline** communicated once the issue is confirmed — critical
  issues (authentication, data exposure) are prioritized above all other work.
- **Credit** in the fix's changelog or release notes, if you would like it
  and it is appropriate to disclose.

### Scope

This policy covers the code in this repository — the FastAPI backend, the
Next.js frontend, and the infrastructure configuration under
`infrastructure/`. It does not cover:

- Vulnerabilities in third-party dependencies (report those upstream, though
  we appreciate a heads-up so we can update)
- Social engineering or physical security issues
- Denial-of-service attacks requiring unrealistic traffic volumes

## Security Practices in This Project

For transparency, here is what the codebase currently does:

- Passwords are hashed with **Argon2id**, not a faster/weaker algorithm.
- Authentication uses **JWT (HS256)** with short-lived access tokens and
  rotating refresh tokens.
- All database queries go through **SQLAlchemy's parameterized query
  interface** — no raw string interpolation into SQL.
- **CORS** is restricted to explicitly configured origins, not wildcarded.
- Security headers (`X-Content-Type-Options`, `X-Frame-Options`,
  `Referrer-Policy`, `Permissions-Policy`) are set on all frontend responses.
- Rate limiting is applied per IP on the reverse proxy layer
  (see `infrastructure/nginx/nginx.conf`).

If you notice a gap between this list and the actual code, that itself is
worth a report.
