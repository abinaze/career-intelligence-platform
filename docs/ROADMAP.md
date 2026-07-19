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

**🟡 Phase 9c — OneDrive + Dropbox backends (in progress)**

Same pattern as 9b, for the remaining two cloud providers.

- ✅ OneDrive: backend OAuth broker (connect/callback/exchange/refresh —
  no disconnect endpoint, Microsoft has no simple per-token revoke API
  for this flow) and frontend (`OneDriveAdapter.ts`, Graph REST client,
  token storage, connect/disconnect UI). Requires Microsoft OAuth
  credentials to actually connect — see
  [`docs/setup/microsoft-oauth-setup.md`](setup/microsoft-oauth-setup.md).
  See [`docs/architecture/byos.md`](architecture/byos.md) for the OAuth
  flow and how it differs from Google Drive's.
- ✅ Dropbox: backend OAuth broker shipped (connect/callback/exchange/
  refresh/disconnect — Dropbox does have a simple token-revoke API,
  unlike Microsoft, so this one has all 5 endpoints like Google Drive's).
  See [`docs/architecture/byos.md`](architecture/byos.md) for the
  Dropbox-specific details (offline access type, revoke-by-access-token).
- 🔲 Dropbox frontend still pending: `DropboxAdapter.ts`, a Dropbox API
  v2 REST client, token storage, connect/disconnect UI.
- Not yet tested against real Microsoft servers (no live credentials
  were available in the sandbox this was built in) — verified via mocked
  backend calls and a real frontend build only.

**🔲 Phase 9d — Local folder export/import**

Manual export-to-file and import-from-file support, for users who want
full offline control without a cloud account.

**🔲 Phase 9e — Onboarding integration + provider switching**

Wires the storage choice into the first-run registration flow (currently
it's only reachable via Settings after account creation), and builds
migration tooling so switching providers later actually moves data instead
of starting fresh.

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

Progress on 9b–9e will be tracked via issues labeled `phase-9-byos`.

### Phase 10 — Free-tier production deployment

Ship a fully deployed, publicly accessible instance using only free-tier
infrastructure:

- **Frontend** — static export deployed via GitHub Pages (or Vercel's free
  tier, evaluated against the BYOS architecture's client-side requirements).
- **Backend** — Hugging Face Spaces (Docker SDK, CPU Basic free tier).
- **Database** — a free-tier managed Postgres provider (Supabase, Railway,
  or Render), used only for data that remains under the platform's
  operational scope even after Phase 9 (e.g., the shared career taxonomy —
  never personal user data).

This phase depends on Phase 9 being far enough along that the deployed
instance reflects the intended privacy model, not the current
all-data-in-Postgres architecture.

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
