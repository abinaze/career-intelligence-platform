# Deployment Guide

## Local Development

### Prerequisites

Install Docker Desktop, Node.js 20 or higher, pnpm 9 or higher, Python 3.12 or higher, and uv.

Install uv with:

```bash
pip install uv
```

### Start Infrastructure

```bash
make dev-up
```

This starts PostgreSQL 16 on port 5432 and Redis 7 on port 6379 only. Run the backend and frontend directly on your host for the fastest local dev loop (hot reload, no rebuild on save).

### Run Migrations

```bash
make migrate
```

### Load Career Data

```bash
make load-onet
```

Seeds the `careers` table with O*NET occupations and builds the FAISS similarity index. Required before `/careers/recommendations` returns results.

### Start Backend

```bash
cd apps/backend
uv run uvicorn src.main:app --reload --port 8000
```

### Start Frontend

```bash
cd apps/frontend
pnpm dev
```

Frontend runs at http://localhost:3000

Backend runs at http://localhost:8000

API docs at http://localhost:8000/docs

## Full Docker Stack (all services containerised)

To run everything — Postgres, Redis, backend, and frontend — in containers:

```bash
make docker-build
make docker-up
```

This uses the `full` Docker Compose profile, which adds `backend` and `frontend` services on top of the base `postgres` + `redis` services. Source directories are bind-mounted so code changes are picked up without rebuilding.

```bash
make docker-logs   # tail all container logs
make docker-down   # stop everything
```

> **Fixed while preparing Phase 10 (production deployment prep):**
> `docker-compose.dev.yml`'s backend and frontend `build.context`/
> `build.dockerfile`/volume paths were wrong — Compose resolves relative
> `context:` paths against *the compose file's own directory*
> (`infrastructure/docker/`), not the directory you run `docker compose`
> from. `context: .` resolved to `infrastructure/docker/` itself, which
> contains neither `apps/backend/pyproject.toml` nor the frontend's
> `pnpm-workspace.yaml` — so `make docker-build` never actually worked.
> Fixed to `context: ../../apps/backend` (backend) and `context: ../..`
> (frontend), with `dockerfile:` and the backend's volume mounts adjusted
> to match. If you were running everything on your host instead of
> `--profile full` (as the Prerequisites section above recommends), this
> never affected you.

## Environment Variables Reference

### Backend Variables

`SECRET_KEY` is required and has no default. It is the JWT signing secret.

`DATABASE_URL` is required and has no default. It is the PostgreSQL connection URL.

`REDIS_URL` is required and has no default. It is the Redis connection URL — used for the BYOS OAuth brokers' short-lived ticket/exchange staging (see `docs/architecture/byos.md`), not for personal user data.

`ENVIRONMENT` is optional and defaults to development.

`LOG_LEVEL` is optional and defaults to INFO.

`ANTHROPIC_API_KEY` is optional. Required only to enable the AI career chat feature (`POST /api/v1/chat/message`). Without it, the rest of the platform works normally and the chat endpoint returns `503`. Get a key at https://console.anthropic.com — see `apps/backend/.env.example`.

`FRONTEND_URL` is required for BYOS to work at all — it's where the three OAuth brokers redirect the browser back to after Google/Microsoft/Dropbox's own callback. Defaults to `http://localhost:3000`; must be the real deployed frontend URL in production.

`GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` / `GOOGLE_OAUTH_REDIRECT_URI`, `MICROSOFT_CLIENT_ID` / `MICROSOFT_CLIENT_SECRET` / `MICROSOFT_OAUTH_REDIRECT_URI`, and `DROPBOX_CLIENT_ID` / `DROPBOX_CLIENT_SECRET` / `DROPBOX_OAUTH_REDIRECT_URI` are all optional — each provider's endpoints return `503` if its pair is unset. See `docs/setup/google-oauth-setup.md`, `docs/setup/microsoft-oauth-setup.md`, and `docs/setup/dropbox-setup.md` for how to obtain real values. The `*_REDIRECT_URI` values must point at wherever the backend is actually deployed, not localhost.

`CELERY_BROKER_URL` / `CELERY_RESULT_BACKEND` exist in settings but nothing in the codebase currently runs a Celery worker (`src/workers/` is an empty scaffold) — safe to leave at their defaults, or even point at the same Redis instance as `REDIS_URL`, for any deployment target in this guide. Worth knowing if you're using a single-database-only Redis provider (see the Upstash note below) and wondering whether you need multi-database support: you don't, yet.

### Frontend Variables

`NEXT_PUBLIC_API_URL` is required. It defaults to http://localhost:8000 in development.

`NEXT_PUBLIC_APP_URL` is required. It defaults to http://localhost:3000 in development.

## Backend Hosting

### What changed, and why

Phase 10 originally documented Hugging Face Spaces as the primary
backend host. Attempting the actual deploy surfaced that HF now
restricts creating new Docker/Gradio Spaces to paid (PRO/Team/Enterprise)
accounts — a policy change from mid-2026, confirmed against HF's own
current docs, not assumed. CPU Basic hardware is still free once a Space
exists; you just can't create one without a paid plan anymore. That sent
this section back to actual research (web search against current 2026
sources, not memory) rather than picking a new platform by assumption —
the same discipline that caught the Railway/Render staleness earlier in
this doc.

**What the research found**, compared head-to-head on the thing that
matters most for a low-traffic personal deployment — sleep/cold start —
since every platform below is otherwise a reasonable, current, genuinely
free option:

| Platform | Sleep behavior | Ops burden | Card required |
|---|---|---|---|
| **Oracle Cloud Always Free VM** | **None** — a real always-on server, not serverless | High — you manage the OS, Docker, security yourself | Yes (identity verification only) |
| Google Cloud Run | Scales to zero by default on the free tier | Low — managed | Yes |
| Koyeb | Disputed between sources; Koyeb's more detailed docs describe free instances scaling to zero after 1hr idle | Low — managed | Sometimes |
| Render | Confirmed sleeps after 15 min, 30-50s wake | Low — managed | No |
| ~~Fly.io~~ / ~~Railway~~ | N/A | N/A | Confirmed no longer meaningfully free |

No option is simultaneously zero-ops, reliably free, and truly
zero-sleep — that combination doesn't exist among current offerings. The
only way to get zero sleep at all is a real server, which is why **Oracle
Cloud's Always Free Ampere A1 VM is the primary documented path** despite
the higher setup burden. Google Cloud Run remains a reasonable
lower-effort alternative if accepting occasional cold starts is fine —
its deploy mechanics aren't documented in this guide in depth, since the
Oracle path was the one actually chosen and built out; the existing
`Dockerfile.backend` production target would work on Cloud Run
unchanged if you go that route instead (it already reads `$PORT`, which
Cloud Run injects, for exactly this kind of portability).

### Oracle Cloud Always Free VM (primary)

Full walkthrough: **[`docs/setup/oracle-cloud-vm-setup.md`](../setup/oracle-cloud-vm-setup.md)**
— account creation, the free Ampere A1 shape (and what to do if you hit
Oracle's well-documented "out of capacity" error), the two separate
firewalls that both have to be opened (a common point of confusion
specific to Oracle Cloud), Docker installation, and bringing up
`infrastructure/docker/docker-compose.oracle-vm.yml` (Postgres + Redis +
backend + Caddy for automatic HTTPS — deliberately not
`docker-compose.prod.yml`, which also runs the frontend for a
fully-self-hosted setup; this path pairs with frontend staying on
Vercel, see below).

Since Postgres and Redis run on the VM itself here, there's no need for
Supabase or Upstash accounts on this path — they're only relevant if you
go with a managed-compute alternative like Cloud Run instead. If you do:
**Postgres — [Supabase](https://supabase.com)** (free tier pauses after
7 days idle, doesn't delete; use the direct/session connection string,
not transaction-mode PgBouncer, which breaks `asyncpg`'s prepared
statements) and **Redis — [Upstash](https://upstash.com)** (genuine
persistent free tier, single-database — which is fine, since nothing in
this codebase's Celery settings is actually wired to a running worker
yet) are still the right picks, verified current as of this phase.

Push-to-deploy from GitHub Actions is `.github/workflows/deploy-oracle-vm.yml`
— SSH into the VM, `git pull`, rebuild and restart just the `backend`
container. See its header comment for one-time setup (a dedicated
deploy-only SSH key, added as GitHub repo secrets).

### Hugging Face Spaces (alternative, requires PRO)

Still fully documented in `infrastructure/huggingface/README.md` for
anyone who already has an HF PRO subscription and would rather use it —
Docker SDK, CPU Basic hardware. The GitHub Actions sync workflow that
used to automate deploys there has been removed (it only ever failed
with "secrets not set," since Spaces created this way now sit behind the
PRO paywall by default); deploying there now means an occasional manual
`git subtree split` push — see that README for the exact command.

## Vercel Deployment for Frontend

Connect your GitHub repository to Vercel.

Set the root directory to apps/frontend.

Set the framework preset to Next.js.

Add these environment variables:

```
NEXT_PUBLIC_API_URL=https://your-hf-space.hf.space
NEXT_PUBLIC_APP_URL=https://your-app.vercel.app
```

No `vercel.json` is required — Vercel's monorepo support (Root Directory setting) auto-detects the pnpm workspace and builds correctly on its own.

**Why Vercel, not GitHub Pages** (the other option this phase's roadmap entry left open, "evaluated against the BYOS architecture's client-side requirements"): this app's `middleware.ts` guards every non-public route by reading the `access_token` cookie server-side — that requires a running Next.js server (Node or Edge runtime). A true static export (what GitHub Pages actually serves — plain files, no server) wouldn't run middleware at all, silently disabling route protection rather than failing loudly. Vercel runs the app's middleware natively, which is why it's the one actually evaluated and recommended here, not a "these are roughly equivalent, pick either" situation.

## Self-Hosted Docker Deployment

As of Phase 10, a `docker-compose.prod.yml` is included — `infrastructure/docker/docker-compose.prod.yml` — closing the gap this section used to describe as "tracked for a future release."

```bash
cp infrastructure/docker/.env.production.example infrastructure/docker/.env.production
# fill in real values in .env.production — see that file's comments

docker compose -f infrastructure/docker/docker-compose.prod.yml \
  --env-file infrastructure/docker/.env.production up -d
```

This brings up Postgres, Redis, the backend (production target, running migrations automatically on start via `apps/backend/docker-entrypoint.sh` — see below), the frontend (production target), and nginx as a reverse proxy in front of both — five containers, one command, all on a single Docker network. TLS isn't set up (nginx listens on port 80 only); either terminate it at a cloud load balancer in front of the host, or add certbot and a 443 listener to `infrastructure/nginx/nginx.conf` yourself.

If you'd rather build and run the images individually instead of via compose:

```bash
docker build -f infrastructure/docker/Dockerfile.backend --target production \
  -t cip-backend:prod apps/backend
docker build -f infrastructure/docker/Dockerfile.frontend --target production \
  -t cip-frontend:prod .
```

Note the different final argument (the **build context**) for each — this used to be documented as `.` (repo root) for both, which is correct for the frontend image but was never actually correct for the backend one: `Dockerfile.backend`'s `COPY pyproject.toml ./` and `COPY . .` assume the build context *is* `apps/backend`, not repo root. Building with `.` as the backend's context would fail with "pyproject.toml not found" — this was a real bug in this guide, not just in `docker-compose.dev.yml` (see the note above); both are fixed now.

### Migrations in production

`apps/backend/docker-entrypoint.sh` runs `alembic upgrade head` before starting uvicorn, every time the container starts — not just on first deploy. `alembic upgrade head` is idempotent, so this is safe to run repeatedly; the alternative (documenting "remember to run migrations manually after every schema change") is exactly the kind of manual step that gets forgotten on a real deployment.
