---
title: Career Intelligence Platform API
emoji: 🧭
colorFrom: blue
colorTo: purple
sdk: docker
app_port: 8000
pinned: false
license: other
---

# Career Intelligence Platform — Backend API

This Space runs the FastAPI backend for the Career Intelligence Platform
(https://github.com/abinaze/career-intelligence-platform). It's deployed
here automatically from the `apps/backend` directory of that repo — see
`.github/workflows/deploy-huggingface.yml` in the main repo for the sync
mechanism. **This Space's own git history is not meant to be edited
directly** — changes should go through the main repo.

## Configuration

This Space needs the following repository secrets set (Settings → Variables
and secrets), matching `apps/backend/.env.example` in the main repo:

- `DATABASE_URL` — a Postgres connection string (see
  `docs/deployment/guide.md`'s Supabase section for the asyncpg/pgbouncer
  pooling caveat)
- `REDIS_URL` — a Redis connection string (see the guide's Upstash section)
- `SECRET_KEY` — JWT signing secret
- `ANTHROPIC_API_KEY` (optional — chat is disabled without it)
- `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` (optional — see
  `docs/setup/google-oauth-setup.md`)
- `MICROSOFT_CLIENT_ID` / `MICROSOFT_CLIENT_SECRET` (optional — see
  `docs/setup/microsoft-oauth-setup.md`)
- `DROPBOX_CLIENT_ID` / `DROPBOX_CLIENT_SECRET` (optional — see
  `docs/setup/dropbox-setup.md`)
- `FRONTEND_URL` — wherever the frontend ends up deployed (Vercel, per
  the main guide)
- `GOOGLE_OAUTH_REDIRECT_URI` / `MICROSOFT_OAUTH_REDIRECT_URI` /
  `DROPBOX_OAUTH_REDIRECT_URI` — this Space's own URL +
  `/api/v1/storage/{provider}/callback`

`/health` reports which of these are actually wired up correctly once set.

## API docs

Once running: `/docs` (Swagger) and `/redoc`.
