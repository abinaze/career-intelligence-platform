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

## Hugging Face Spaces Deployment for Backend

Hugging Face Spaces supports FastAPI via the Docker SDK. As of Phase 10, this is automated — pushing to `main` (when `apps/backend/**` changes) triggers `.github/workflows/deploy-huggingface.yml`, which syncs `apps/backend` to the Space's own git repo via a `git subtree split` push. See that workflow's header comment for one-time setup (creating the Space, adding `HF_TOKEN`/`HF_SPACE_ID` as GitHub Actions secrets).

The workflow stages two Hugging-Face-specific files into a local, never-pushed-to-`origin` commit before syncing: `infrastructure/docker/Dockerfile.backend` copied to `apps/backend/Dockerfile` (Spaces expect a Dockerfile at the Space repo's root), and `infrastructure/huggingface/README.md` copied to `apps/backend/README.md` (the Space's *own* README, with the YAML config header Spaces require — deliberately kept separate from `apps/backend/README.md`'s real package documentation, which this never touches on the main branch).

**Hardware**: CPU Basic (the free tier). **Cold starts**: free Spaces go to sleep after a period of inactivity and take a noticeable moment to wake back up on the next request — expected behavior, not a misconfiguration, worth knowing about before assuming something's broken if the first request after a while is slow.

### Space secrets

Set these under the Space's Settings → Variables and secrets (not the GitHub Actions secrets used for the sync workflow — these are separate):

```
SECRET_KEY=your-production-secret
DATABASE_URL=your-postgres-connection-url
REDIS_URL=your-redis-connection-url
ENVIRONMENT=production
FRONTEND_URL=https://your-frontend.vercel.app
ANTHROPIC_API_KEY=your-anthropic-key                          # optional, enables chat
GOOGLE_CLIENT_ID=... / GOOGLE_CLIENT_SECRET=...                # optional, enables Google Drive BYOS
GOOGLE_OAUTH_REDIRECT_URI=https://your-space.hf.space/api/v1/storage/google-drive/callback
MICROSOFT_CLIENT_ID=... / MICROSOFT_CLIENT_SECRET=...          # optional, enables OneDrive BYOS
MICROSOFT_OAUTH_REDIRECT_URI=https://your-space.hf.space/api/v1/storage/onedrive/callback
DROPBOX_CLIENT_ID=... / DROPBOX_CLIENT_SECRET=...              # optional, enables Dropbox BYOS
DROPBOX_OAUTH_REDIRECT_URI=https://your-space.hf.space/api/v1/storage/dropbox/callback
```

`GET /health` on the running Space reports which of the optional pieces are actually wired up (`chat`, `google_drive_storage`, `onedrive_storage`, `dropbox_storage`, plus `database` and `redis` connectivity) — check it first if something isn't working after a deploy, before assuming the build itself failed.

### Free database & cache options (verified current as of this phase)

- **Postgres — [Supabase](https://supabase.com)** (recommended): genuine persistent free tier, 500MB. **Two things worth knowing:** (1) free projects pause after 7 days of inactivity — they don't get deleted, just need a dashboard visit to wake back up, which matters for a demo instance nobody's actively using; (2) Supabase's default pooled connection string uses PgBouncer in transaction mode, which doesn't support prepared statements the way `asyncpg` (this project's driver) expects by default — use Supabase's **direct connection** string (or the "Session" pooling mode, not "Transaction") for `DATABASE_URL`, or you'll see cryptic prepared-statement errors that have nothing to do with your actual schema or credentials.
- **~~Render free Postgres~~** — not recommended: free databases are automatically deleted after 30 days, with no backups. Fine for a throwaway test, not for anything meant to persist. ~~Railway free tier~~ — no longer has a genuine free tier as of this writing; it's a one-time trial credit followed by a paid minimum. Both claims corrected here after appearing in an earlier version of this guide that hadn't been checked against current pricing.
- **Redis — [Upstash](https://upstash.com)** (recommended): genuine persistent free tier (500K commands/month, 256MB), no credit card, serverless — a good match for this app's actual Redis usage, which is low-volume, short-TTL OAuth staging keys, not a cache under heavy load. Note: Upstash (like most managed Redis-as-a-service) is single-database — no `SELECT 1`/`SELECT 2` — which is exactly why the Celery variables above don't matter yet; `REDIS_URL` (database 0, implicitly) is the only one this app's current functionality actually reads from.

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
