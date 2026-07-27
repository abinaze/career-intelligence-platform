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

> **Not the primary deployment path.** Hugging Face restricted creating
> new Docker/Gradio Spaces to paid (PRO/Team/Enterprise) accounts as of
> mid-2026 — CPU Basic hardware itself is still free once a Space
> exists, but you can no longer create one without a paid plan. The
> primary documented path is now a self-hosted Oracle Cloud Always Free
> VM — see `docs/setup/oracle-cloud-vm-setup.md`. This file (and the
> Docker SDK config below) is kept for anyone who already has HF PRO and
> would rather use it; there's no longer a GitHub Actions workflow that
> syncs to it automatically (it's been removed — see
> `docs/deployment/guide.md` for why), so deploying here means pushing
> to this Space's git remote yourself.

# Career Intelligence Platform — Backend API

This Space runs the FastAPI backend for the Career Intelligence Platform
(https://github.com/abinaze/career-intelligence-platform). It is **not**
kept in sync automatically anymore — see the note at the top of this
file for why. To deploy a change here manually: `git subtree split
--prefix=apps/backend -b hf-space-deploy` from the main repo, then push
that branch to this Space's git remote as `main`.

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
