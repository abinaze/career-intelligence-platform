# Koyeb setup (backend hosting, no credit card required — tried, didn't work)

**Status: attempted and reported not working; kept documented, not
recommended as a starting point.** Originally chosen over Render for the
better theoretical chance at avoiding sleep/cold starts (Koyeb's sleep
behavior was — and still is — genuinely unsettled between sources,
unlike Render's confirmed 15-minute sleep). A real deployment attempt on
Koyeb didn't work; the exact symptom (build failure, runtime crash, or
something else) was never captured, so this page can't tell you what
went wrong or promise the fix below actually addresses it. **Render is
now the primary path** — see `docs/setup/render-setup.md` — precisely
because it's the one of the two that hasn't been tried and failed yet.

This guide is left here in full for two reasons: it's still a real,
no-credit-card candidate if Render also doesn't work for you, and the
`apps/backend/Dockerfile` duplicate this guide originally motivated is
now used by both platforms' setup guides. Not tested end-to-end against
a live Koyeb account while writing this update either (no account was
available in the environment this was built in) — based on Koyeb's own
current documentation, which is detailed and specific enough to follow
directly, but treat any real walkthrough as the actual test, not this
page.

## 1. Create a Koyeb account

[app.koyeb.com](https://app.koyeb.com) — sign up with GitHub or email.
No credit card requested at signup for the free (Hobby) plan.

## 2. Create the Web Service

**Create Web Service → GitHub** (authorize Koyeb to access your
repositories if this is the first time) → select
`abinaze/career-intelligence-platform`.

### Builder configuration

- **Builder**: Dockerfile (not the default Buildpack builder — we want
  the real, tested Dockerfile, not Koyeb guessing at a Python setup).
- **Work directory**: `apps/backend`. This is Koyeb's own supported
  mechanism for monorepos — it sets the build context to this
  subdirectory, matching exactly what `Dockerfile.backend`'s own `COPY`
  instructions already assume (see `docs/deployment/guide.md`'s note on
  this same assumption tripping up the Docker Compose files earlier in
  this project). Per Koyeb's own monorepo docs, setting a work directory
  excludes the rest of the repository from the build environment — so
  the Dockerfile itself has to live inside `apps/backend`, not out at
  `infrastructure/docker/`.
- **Dockerfile location**: leave at the default (`Dockerfile`). This
  resolves to `apps/backend/Dockerfile` — a hand-synced duplicate of
  `infrastructure/docker/Dockerfile.backend`, kept specifically for this
  reason. See that file's own header comment for what "hand-synced"
  means in practice (no build-time mechanism keeps the two in sync, only
  the comment). An earlier version of this guide tried a `../
  infrastructure/docker/Dockerfile.backend` relative path to avoid the
  duplicate entirely; that was never confirmed to work against Koyeb's
  real UI, and given the "rest of repo excluded" behavior above, it
  likely wouldn't have — the duplicate is the reliable option.
- **Docker build target**: `production` (this Dockerfile is multi-stage;
  Koyeb needs to know which stage to actually run).

### Exposing the service

- **Ports**: `8000`, routed to `/`.
- Leave **Privileged** off — that flag is only for the unusual case of
  running Docker Compose *inside* a Koyeb service; we're deploying the
  backend directly.

### Instance & region

- **Instance**: Free (Hobby) — 0.1 vCPU / 512MB RAM. This is genuinely
  thin for a Python app with `numpy`/`faiss-cpu`/`sentence-transformers`
  in its dependency tree — workable at rest since the actual embedding
  model is lazy-loaded (see `docs/architecture/byos.md`'s embeddings
  note), but worth watching memory usage under real load; if the service
  gets OOM-killed repeatedly, that's the free tier's ceiling, not a bug
  in the app.
- **Region**: pick whichever is closest to you; Koyeb's free tier is
  currently limited to Washington D.C. or Frankfurt.

### Environment variables

Add these under the service's **Environment variables** section (same
names as every other deployment path documented in this project —
cross-checked against `src/core/config/settings.py`, not guessed):

```
SECRET_KEY=your-production-secret
DATABASE_URL=your-supabase-connection-string
REDIS_URL=your-upstash-connection-string
ENVIRONMENT=production
FRONTEND_URL=https://your-frontend.vercel.app
ANTHROPIC_API_KEY=your-anthropic-key                          # optional, enables chat
GOOGLE_CLIENT_ID=... / GOOGLE_CLIENT_SECRET=...                # optional, enables Google Drive BYOS
GOOGLE_OAUTH_REDIRECT_URI=https://your-app-name.koyeb.app/api/v1/storage/google-drive/callback
MICROSOFT_CLIENT_ID=... / MICROSOFT_CLIENT_SECRET=...          # optional, enables OneDrive BYOS
MICROSOFT_OAUTH_REDIRECT_URI=https://your-app-name.koyeb.app/api/v1/storage/onedrive/callback
DROPBOX_CLIENT_ID=... / DROPBOX_CLIENT_SECRET=...              # optional, enables Dropbox BYOS
DROPBOX_OAUTH_REDIRECT_URI=https://your-app-name.koyeb.app/api/v1/storage/dropbox/callback
```

Neither Supabase nor Upstash requires a credit card either — both were
re-verified specifically because of that constraint, not just carried
over from earlier research. See `docs/deployment/guide.md`'s database
section for the Supabase connection-string gotcha (use the direct/session
connection string, not transaction-mode PgBouncer — it breaks `asyncpg`'s
prepared statements).

`your-app-name.koyeb.app` is Koyeb's own auto-assigned domain, shown once
the service is created — you don't need a custom domain for this path
the way the Oracle VM guide's Caddy setup does, since Koyeb issues a free
SSL certificate on its own subdomain automatically.

## 3. Deploy

Click **Deploy**. Koyeb builds the Dockerfile and deploys automatically;
build logs are visible live in the control panel. Once healthy, check
`https://your-app-name.koyeb.app/health` — it reports which optional
pieces (chat, each BYOS provider) are actually wired up.

## 4. Continuous deployment — already automatic

Unlike the Hugging Face Spaces path (which needed a custom
`git subtree split` GitHub Actions workflow — removed, since it no
longer worked without paying) or the Oracle VM path (SSH-based push-to-deploy,
`.github/workflows/deploy-oracle-vm.yml`), **Koyeb's GitHub
integration deploys automatically on every push to `main`** once
connected in step 2 — no extra workflow file needed for this path. If you
ever want to restrict *when* it redeploys (e.g. only on
`apps/backend/**` changes), that's configured in the service's Git
settings on Koyeb's side, not in this repo.

## Migrations

`apps/backend/docker-entrypoint.sh` runs `alembic upgrade head` before
starting uvicorn on every container start — same as every other
deployment path in this project. Nothing Koyeb-specific needed here.

## If the free instance sleeps in practice

If you find it does sleep (this guide's honesty note above: sources
disagree), the practical mitigation without paying is an external uptime
pinger (e.g. a free [UptimeRobot](https://uptimerobot.com) monitor
hitting `/health` every few minutes) — keeps the instance warm as a side
effect of just checking it's up. Worth trying only if real usage shows
actual cold starts; no need to set this up preemptively.
