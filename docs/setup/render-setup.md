# Render setup (backend hosting, no credit card required)

Chosen after Koyeb was tried and its deployment didn't work — the exact
symptom was never captured (build failure, runtime crash, or something
else entirely), so this isn't "Koyeb is broken," it's "Koyeb didn't work
once, for an unconfirmed reason, and Render is the other card-free
candidate that research already confirmed." See
`docs/deployment/guide.md`'s comparison table for the full reasoning
that narrowed the field to these two in the first place.

Verified against Render's own current documentation (fetched live, not
recalled from training data) while writing this — **not** tested
end-to-end against a real Render account, since no account was available
in the environment this was built in. Treat your first real walkthrough
as the actual test, the same caveat as every other deployment guide in
this project.

Render's free tier: no credit card at signup, 750 instance-hours/month
for web services (enough for one service to run continuously all month —
one container at ~730-744 hours/month fits inside that budget), managed
TLS and a free `onrender.com` subdomain included, and — the one real
trade-off versus Koyeb — **confirmed sleep after 15 minutes idle**, with
a 30-60 second cold start on the next request. Koyeb's sleep behavior
was genuinely disputed between sources; Render's isn't — this is a
known, not a maybe.

## 1. Create a Render account

[dashboard.render.com](https://dashboard.render.com) — sign up with
GitHub or email. No credit card requested for the free plan.

## 2. Create the Web Service

**New → Web Service** → connect your GitHub account if this is the
first time → select `abinaze/career-intelligence-platform`.

### Build & Deploy configuration

- **Root Directory**: `apps/backend`. Render calls this "Root
  Directory," not "Work directory" (Koyeb's term) — same concept: every
  other path setting below is resolved relative to this one, and files
  outside it aren't part of the build.
- **Runtime**: **Docker** (Render auto-detects this once a Dockerfile is
  found; if it offers a native Python buildpack instead, switch it
  manually — we want the real, tested Dockerfile, not Render guessing at
  a Python setup).
- **Dockerfile Path**: leave at the default (`Dockerfile`). With Root
  Directory set to `apps/backend`, this resolves to
  `apps/backend/Dockerfile` — the hand-synced duplicate of
  `infrastructure/docker/Dockerfile.backend` kept specifically for
  PaaS providers with this single-root-directory model (see that file's
  own header comment for why it exists and isn't just `../
  infrastructure/docker/Dockerfile.backend`).

  Worth knowing even though it isn't used here: Render's Dockerfile Path
  and **Docker Build Context Directory** fields are independently
  configurable (confirmed against Render's current monorepo-support
  docs), so Render — unlike Koyeb — could point directly at
  `infrastructure/docker/Dockerfile.backend` with a context override of
  `apps/backend`, no duplicate needed. This guide uses the duplicate
  anyway, so this setup and the Koyeb one follow the same mental model
  ("Root/Work directory = apps/backend, Dockerfile = default") instead
  of two different ones for what's otherwise the same build.
- **Docker Build Context Directory**: leave at the default (resolves to
  the Root Directory, `apps/backend` — exactly what `COPY pyproject.toml
  ./` and `COPY . .` in the Dockerfile already assume).
- **Docker Command**: leave blank — the Dockerfile's own `ENTRYPOINT`
  (`docker-entrypoint.sh`, which runs migrations then starts uvicorn)
  handles this; don't override it here.

### Instance type

- **Instance Type**: **Free** — 0.1 CPU / 512MB RAM. Same thin-resource
  caveat as Koyeb's free instance: workable at rest since the embedding
  model is lazy-loaded (see `docs/architecture/byos.md`'s embeddings
  note), but watch memory under real load. If it gets OOM-killed
  repeatedly, that's the free tier's ceiling, not an app bug.
- **Region**: pick whichever is closest to you in the dropdown.

### Health checks

- **Health Check Path**: `/health`. This is a native Render field for
  Docker web services — set it so Render can tell a genuinely broken
  deploy from one that's just slow to start, instead of routing traffic
  to a container that isn't ready yet.

### Environment variables

Add these under **Environment** (same names as every other deployment
path documented in this project — cross-checked against
`src/core/config/settings.py`, not guessed):

```
SECRET_KEY=your-production-secret
DATABASE_URL=your-supabase-connection-string
REDIS_URL=your-upstash-connection-string
ENVIRONMENT=production
FRONTEND_URL=https://your-frontend.vercel.app
ANTHROPIC_API_KEY=your-anthropic-key                          # optional, enables chat
GOOGLE_CLIENT_ID=... / GOOGLE_CLIENT_SECRET=...                # optional, enables Google Drive BYOS
GOOGLE_OAUTH_REDIRECT_URI=https://your-app-name.onrender.com/api/v1/storage/google-drive/callback
MICROSOFT_CLIENT_ID=... / MICROSOFT_CLIENT_SECRET=...          # optional, enables OneDrive BYOS
MICROSOFT_OAUTH_REDIRECT_URI=https://your-app-name.onrender.com/api/v1/storage/onedrive/callback
DROPBOX_CLIENT_ID=... / DROPBOX_CLIENT_SECRET=...              # optional, enables Dropbox BYOS
DROPBOX_OAUTH_REDIRECT_URI=https://your-app-name.onrender.com/api/v1/storage/dropbox/callback
```

Neither Supabase nor Upstash requires a credit card either — see
`docs/deployment/guide.md`'s database section for the Supabase
connection-string gotcha (use the direct/session connection string, not
transaction-mode PgBouncer — it breaks `asyncpg`'s prepared statements).

`your-app-name.onrender.com` is Render's own auto-assigned domain, shown
once the service is created — no custom domain needed for this path, TLS
is issued automatically on the Render subdomain.

## 3. Deploy

Click **Create Web Service**. Render builds the Dockerfile and deploys
automatically; build logs stream live in the dashboard. Once healthy,
check `https://your-app-name.onrender.com/health` — it reports which
optional pieces (chat, each BYOS provider) are actually wired up.

## 4. Continuous deployment — already automatic

Same as Koyeb: **Render's GitHub integration auto-deploys on every push**
to the connected branch (`main` by default) once the service is created —
no custom GitHub Actions workflow needed for this path, unlike the
Oracle VM path's SSH-based one (`.github/workflows/deploy-oracle-vm.yml`)
or the removed Hugging Face Spaces `git subtree split` workflow.

If you want to restrict *when* it redeploys (e.g. only on
`apps/backend/**` changes) so unrelated frontend-only commits don't
trigger a rebuild, that's Render's **Build Filters** setting — Settings →
Build & Deploy → Build Filters — configured on Render's side, not in
this repo.

## Migrations

`apps/backend/docker-entrypoint.sh` runs `alembic upgrade head` before
starting uvicorn on every container start — same as every other
deployment path in this project. Nothing Render-specific needed here.

## The sleep trade-off, and what to do about it

Unlike Koyeb's disputed sleep behavior, Render's is confirmed: **the
free instance sleeps after 15 minutes of no requests**, and the next
request pays a 30-60 second cold start while it wakes back up. This is
real, not a maybe — plan for it rather than being surprised by it.

If that's a problem for how you're using this (e.g. demoing it live to
someone), the practical mitigation without paying is the same one
documented for Koyeb: an external uptime pinger (e.g. a free
[UptimeRobot](https://uptimerobot.com) monitor hitting `/health` every
few minutes) keeps the instance warm as a side effect of just checking
it's up. Worth setting up only if the cold start actually matters for
your use case — it doesn't fix anything for the platform's actual users
in a real deployment, it just avoids the first visitor of the day
eating the wake-up latency.

## If this also doesn't work

Per `docs/ROADMAP.md`'s Phase 10 notes: if Render fails too, that's a
second independent-platform failure after Koyeb. Given how much research
already went into platform selection, a repeat failure across two
different platforms points toward something app- or Dockerfile-specific
rather than a bad platform choice each time — worth reading the actual
build/runtime logs directly (both platforms show them live in their
dashboards) rather than pivoting to a third platform blindly. The
`apps/backend/Dockerfile` vs `infrastructure/docker/Dockerfile.backend`
duplication (see that file's header comment) is one concrete thing worth
double-checking stays in sync if you edit one and not the other.
