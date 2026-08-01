# Roadmap

This project has been built in discrete, reviewable phases. This document
tracks what has shipped and what's planned, so contributors and users have
an honest picture of the project's current state versus its direction.

For the philosophy behind *why* the platform is built this way — not just
*what* is built — see [`docs/VISION.md`](./VISION.md).

## Shipped

| Phase | Scope |
|---|---|
| **1 — Foundation** | Monorepo scaffold, database schema, Alembic migrations, CI pipeline |
| **2 — Recommendation Engine** | Sentence-transformer embeddings, FAISS similarity search, multi-factor ranker, explainability engine, O*NET data loader |
| **3 — Assessment UI** | Full interactive assessment flow — question cards, progress tracking, radar-chart results |
| **4 — Dashboard & Careers UI** | Live dashboard, ranked career recommendation cards with expandable explanations, route protection middleware |
| **5 — Settings** | Profile editing with live completeness scoring, account details, password change UI, account danger zone |
| **6 — AI Career Chat** | Chat endpoint grounded in the user's psychometric profile, full conversational UI |
| **7 — Production Readiness (infra)** | Multi-stage Docker builds for both apps, nginx reverse proxy config, corrected environment documentation |
| **8 — Professional Documentation & Licensing** | This README rewrite, license change to PolyForm Noncommercial, contribution guidelines, security policy, issue/PR templates |
| **9a — BYOS: Storage Adapter Pattern + Local Device Storage** | `StorageAdapter` interface, `PlatformAdapter` (existing DB-backed behavior, unchanged), `LocalDeviceAdapter` (IndexedDB-backed), 3 new stateless backend endpoints for compute-without-persistence, Settings → Storage tab, storage selection UI |

## In progress / planned

### Phase 9 — Bring-Your-Own-Storage (BYOS) architecture

The long-term direction for this project is to **not retain a copy of users'
personal career and psychometric data on the platform's own servers.**
Instead, a user chooses where their data lives. This is being built as a
sequence of sub-phases rather than one large change — see
[`docs/architecture/byos.md`](./architecture/byos.md) for the full technical
design of what's shipped so far.

**✅ Phase 9a — Storage adapter pattern + Local Device storage (shipped)**

Introduced the `StorageAdapter` interface on the frontend and two
implementations: `PlatformAdapter` (wraps the existing DB-backed endpoints,
zero behavior change for the default experience) and `LocalDeviceAdapter`
(browser IndexedDB, opt-in via Settings → Storage). Added three stateless
backend endpoints (`/stateless/questions`, `/stateless/score`,
`/stateless/recommendations`) that compute a result from client-supplied
data without persisting it — reusing the exact same scoring and
recommendation logic as the DB-backed path via a shared
`recommend_from_data()` core method, not a duplicated implementation.

**✅ Phase 9b — Google Drive backend (shipped)**

Same `StorageAdapter` interface, a `GoogleDriveAdapter` implementation:
OAuth connection flow, a data file read from and written to the user's own
Drive `appDataFolder` space. **Not end-to-end encrypted** — an intentional,
documented scope limitation of this phase, not a bug (see
[`docs/architecture/byos.md`](architecture/byos.md)).

- ✅ Backend OAuth broker: five endpoints implementing a
  ticket/exchange-staged handshake so the backend never persists Drive
  tokens (see the API reference's
  [Storage — Google Drive (BYOS) section](api/reference.md)).
- ✅ Frontend: `GoogleDriveAdapter.ts`, the raw Drive REST client, token
  storage, `GoogleDriveConnect.tsx`, and settings-tab routing. Requires
  Google OAuth credentials to actually connect — see
  [`docs/setup/google-oauth-setup.md`](setup/google-oauth-setup.md).
- Not yet tested against real Google servers (no live credentials were
  available in the sandbox this was built in) — verified via mocked
  backend calls only. First real-credential smoke test is the user's
  responsibility per the setup guide.

**✅ Phase 9c — OneDrive + Dropbox backends and frontends (shipped)**

Same pattern as 9b, for the remaining two cloud providers. All three
cloud providers (Google Drive, OneDrive, Dropbox) are now fully wired:
backend OAuth broker + frontend adapter + connect/disconnect UI.

- ✅ OneDrive: backend OAuth broker (connect/callback/exchange/refresh —
  no disconnect endpoint, Microsoft has no simple per-token revoke API
  for this flow) and frontend (`OneDriveAdapter.ts`, Graph REST client,
  token storage, connect/disconnect UI). Requires Microsoft OAuth
  credentials to actually connect — see
  [`docs/setup/microsoft-oauth-setup.md`](setup/microsoft-oauth-setup.md).
- ✅ Dropbox: backend OAuth broker (connect/callback/exchange/refresh/
  disconnect — Dropbox does have a simple token-revoke API, unlike
  Microsoft, so this one has all 5 endpoints like Google Drive's) and
  frontend (`DropboxAdapter.ts`, Dropbox API v2 REST client, token
  storage, connect/disconnect UI with a real backend-revoke disconnect).
  Requires Dropbox app credentials to actually connect — see
  [`docs/setup/dropbox-setup.md`](setup/dropbox-setup.md).
- See [`docs/architecture/byos.md`](architecture/byos.md) for the OAuth
  flow details and how each provider differs from Google Drive's.
- Not yet tested against real Microsoft or Dropbox servers (no live
  credentials were available in the sandbox this was built in) —
  verified via mocked backend calls and real frontend builds
  (`tsc`/`eslint`/`next build`) only. First real-credential smoke test
  for all three providers is the user's responsibility per their
  respective setup guides.

**✅ Phase 9d — Manual export/import (shipped)**

Export-to-file and import-from-file, available in Settings → Storage
regardless of which provider is active. Built entirely on Phase 9e's
`exportSnapshot()`/`restoreSnapshot()` — not a sixth `StorageAdapter`.
`local_folder` stays `coming_soon`: a true live folder adapter would need
the File System Access API, which is Chromium-only and doesn't reliably
persist directory permissions across sessions — a worse, inconsistent
experience under the same UI as the other four adapters. See
[`docs/architecture/byos.md`](architecture/byos.md) for the full reasoning.

**✅ Phase 9e — Onboarding integration + provider switching (shipped)**

Wires the storage choice into the first-run registration flow (a new
`/onboarding/storage` page, shown once right after signup — not a gate,
just a detour before `/dashboard`), and builds migration tooling so
switching providers later actually moves data instead of starting fresh.

- Every `StorageAdapter` gained `exportSnapshot()`/`restoreSnapshot()`;
  `useStorageProvider.selectProvider()` migrates data automatically
  before switching. See
  [`docs/architecture/byos.md`](architecture/byos.md) for the full design,
  including one honest, one-directional gap: migrating an assessment
  *into* platform storage isn't possible without new backend work, and
  the UI says so rather than pretending.
- Recommendations are deliberately not part of what migrates — they're
  a derived cache, recomputed for free from the assessment.

**Trade-offs being designed around**, and documented openly rather than
glossed over:

- Instant cross-device sync for "this device" storage is not possible by
  definition — the data doesn't leave the device.
- Sharing a profile or recommendation set with someone else (e.g., a career
  counsellor) requires either the user's chosen cloud provider's sharing
  mechanism, or a manual export.
- Account recovery, if a user loses access to their chosen storage and has
  no backup, is not something the platform can solve on their behalf under
  this model — this is a deliberate trade-off of the privacy-first design,
  not an oversight.

All of Phase 9 (9a–9e) has shipped. The one gap that spans all of it:
none of the three cloud providers (Google Drive, OneDrive, Dropbox) have
been tested against a real account — every phase was verified via mocked
HTTP calls, real type-checks, and real production builds, but never a
live OAuth round-trip. That's the next thing to actually do here, ahead
of any new phase.

### Phase 10 — Free-tier production deployment

**🟡 Deployment prep shipped; actual live deployment not attempted.**

Ship a fully deployed, publicly accessible instance using only free-tier
infrastructure:

- **Frontend** — Vercel's free tier. GitHub Pages was evaluated, not just
  assumed away: this app's `middleware.ts` guards routes by reading a
  cookie server-side, which needs a running Next.js server (Node/Edge
  runtime) — a true static export (what GitHub Pages actually serves)
  wouldn't run middleware at all, silently disabling route protection
  rather than failing loudly. Vercel runs middleware natively, which is
  why it's the one actually chosen. See
  [`docs/deployment/guide.md`](deployment/guide.md).
- **Backend** — **Koyeb**, the actual chosen path (see the four-attempt
  sequence below for why it took this long to land here). Postgres on
  Supabase, Redis on Upstash — neither requires a credit card, confirmed
  specifically because that constraint ended up mattering.
- **Backend, documented alternative for later** — Oracle Cloud's Always
  Free Ampere A1 VM, self-hosting Postgres + Redis + the backend behind
  Caddy. The *better* answer once a credit card is available (genuinely
  zero sleep, unlike Koyeb's disputed behavior) — kept fully documented,
  not primary, purely because of a constraint outside the code itself.
- **Self-hosting alternative** — `infrastructure/docker/docker-compose.prod.yml`,
  for anyone who'd rather run the frontend on the same box too instead
  of splitting it to Vercel.

**What actually happened, across four attempts, in order — worth reading
as a sequence, not just the final answer, since each step's reasoning is
what makes the final choice defensible rather than arbitrary:**

1. **Hugging Face Spaces.** Docker SDK, CPU Basic hardware, automated via
   a `git subtree split` GitHub Actions workflow. Documented and built as
   the primary path.
2. **Hit a real wall trying to actually use it**: Hugging Face restricted
   *creating* new Docker/Gradio Spaces to paid (PRO/Team/Enterprise)
   accounts sometime around mid-2026 — confirmed against HF's own
   current docs and multiple corroborating reports of people blindsided
   by it with no changelog notice. This wasn't something Phase 10's
   original research should have caught — it changed after that work was
   done — but it genuinely blocked the documented path once someone
   tried to follow it. The now-nonfunctional sync workflow was removed
   rather than left in place failing the same way every time.
3. **Researched every current free-tier Docker host** (Cloud Run, Koyeb,
   Render, Fly.io, Railway, Oracle Cloud) via live web search rather than
   assumption — the same discipline that had already caught the stale
   Railway/Render claims. **Finding: nothing is simultaneously zero-ops,
   reliably free, and truly zero-sleep.** Chose Oracle Cloud's Always
   Free VM — the only genuinely zero-sleep option, trading managed-platform
   simplicity for an actual server. Built out fully: compose file, Caddy
   config, SSH deploy workflow, a setup guide covering Oracle-specific
   gotchas (two separate firewalls that both have to be opened; the
   well-known "out of capacity" error on the free ARM shape).
4. **A harder constraint surfaced after that was built: no credit card
   available at all.** Both Oracle (identity verification) and Google
   Cloud Run (GCP's billing account, even for free-tier usage) require
   one. That's not a preference to route around — it eliminated both of
   the two best sleep-behavior options outright. Went back to the same
   research discipline specifically for card-free platforms; confirmed
   Koyeb and Render as the two real remaining candidates (explicitly
   distrusting several other results — "SnapDeploy," "GratisVPS," and
   near-identical marketing copy syndicated across multiple "independent"
   review sites — as likely SEO content-farm material with no
   independent verification, rather than passing them through as
   legitimate options). **Koyeb is the final choice**: best remaining
   shot at avoiding sleep, at the cost of thin resources (0.1 vCPU/512MB)
   and a sleep-behavior question that's genuinely unresolved between
   sources — stated as such, not smoothed over.

Given step 4, Supabase and Upstash are back in the primary path (they'd
briefly been dropped when Oracle's VM was the plan, since that
self-hosts its own Postgres/Redis) — both re-verified card-free
specifically because of the new constraint, not just carried over.

**Real bugs found and fixed while preparing this, unrelated to any of the
BYOS work**: `docker-compose.dev.yml`'s build `context:`/`dockerfile:`
paths for both backend and frontend were wrong (Compose resolves
relative paths against the compose file's own directory, not wherever
`docker compose` is invoked from) — `make docker-build` never actually
worked via the `full` profile. The backend's build-context assumption was
also wrong in this guide's own manually-documented `docker build`
command. Both fixed; see `docs/deployment/guide.md` for the detail.

**What "prep" means here, honestly**: Docker configs, CI/CD workflows,
and documentation are all in place and internally consistent — verified
by careful manual tracing of every path and env var against the real
`settings.py` (catching a real `JWT_SECRET`/`SECRET_KEY` naming mismatch
of my own along the way, more than once, since it's easy to reintroduce a
typo when rewriting from a mental template of an earlier file), not by
an actual `docker build`, a live deployment, or a real account on any of
Koyeb/Oracle/Supabase/Upstash (none were available while building this).
**Nothing has actually been deployed.** The first real test of any of
this — including whether Koyeb's console still matches
`docs/setup/koyeb-setup.md`'s steps, and whether its sleep behavior turns
out to match either disputed claim — is someone actually running it.

### Phase 11 — Extended AI engines

The platform's AI layer is designed around seven cooperating engines (see
[`docs/VISION.md`](./VISION.md#technical-architecture-built-versus-planned)
for the full rationale). Four are built today: Psychometric, Recommendation,
Explainability, and a partial Career Ontology integration (O*NET seed data
only, no dedicated ontology service yet). Three are planned:

- **Behavioral Engine** — pattern recognition from how a user interacts
  with the platform over time, rather than a one-time assessment snapshot.
- **Skill Gap Engine** — compares a user's current skills against a target
  career's actual requirements and surfaces the specific, actionable gap.
- **Labor Market Engine** — deeper market-signal integration beyond the
  current static outlook percentile field — real-time demand signals and
  regional variation.

These are listed here, rather than in the README's feature table, precisely
because they are not built. This phase has no committed start date; it
follows Phases 9 and 10.

## How to follow along

- Each phase above corresponds to a merged pull request or a dedicated
  feature branch — see the repository's [pull request history](https://github.com/abinaze/career-intelligence-platform/pulls?q=is%3Apr).
- Design discussion for upcoming phases happens in [Issues](https://github.com/abinaze/career-intelligence-platform/issues)
  tagged with the relevant phase label.
- This document is updated at the start and completion of each phase.
