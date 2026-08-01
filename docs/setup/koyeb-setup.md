# Koyeb setup (backend hosting, no credit card required)

Chosen after Oracle Cloud and Google Cloud Run both turned out to
require a credit card on file (Oracle for identity verification, Google
for the billing account a free-tier project still needs) — a hard
constraint that ruled both out. Koyeb and Render were the two remaining
options confirmed not to require one; Koyeb was picked for the better
chance at avoiding sleep/cold starts — though that's genuinely unsettled
between sources, see the honesty note in `docs/deployment/guide.md`'s
comparison table. Not tested end-to-end against a live Koyeb account
while writing this (no account was available in the environment this was
built in) — based on Koyeb's own current documentation, which is
detailed and specific enough to follow directly, but treat your first
real walkthrough as the actual test.

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
  this project).
- **Dockerfile location**: `../infrastructure/docker/Dockerfile.backend`
  (relative to the work directory above). This relies on Docker's `-f`
  flag being able to point outside the build context — which is normal,
  standard Docker behavior (only `COPY`/`ADD` sources are restricted to
  the context; the Dockerfile's own location isn't) — but it's the one
  part of this guide that's an inference from how Docker works rather
  than a confirmed screenshot of Koyeb's own UI accepting a `../` path.
  **If Koyeb's Dockerfile location field rejects that path**: commit a
  plain copy of `infrastructure/docker/Dockerfile.backend` to
  `apps/backend/Dockerfile` instead, and set Dockerfile location to just
  `Dockerfile` (the default). Worth trying the relative path first since
  it keeps one canonical Dockerfile instead of two copies to keep in sync.
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
