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

## In progress / planned

### Phase 9 — Bring-Your-Own-Storage (BYOS) architecture

The long-term direction for this project is to **not retain a copy of users'
personal career and psychometric data on the platform's own servers.**
Instead, at onboarding, a user chooses where their data lives:

- **This device** — private, browser-based storage (e.g., IndexedDB), never
  leaves the device.
- **Google Drive / Microsoft OneDrive / Dropbox** — the user's own cloud
  storage account, connected via OAuth, holding an encrypted data file the
  platform reads and writes to on the user's behalf.
- **Local folder** — export and import a data file manually, giving the user
  full offline control.

**What this means architecturally:** the backend's role shifts from "owner
of a persistent users' data store" to "stateless compute over data the
client supplies or fetches from the user's chosen provider." This is a
significant redesign of the profile, assessment, and recommendation data
paths — not a small feature flag — and is being tracked as its own phase
rather than rushed into the existing architecture.

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

This phase is under active design. Progress will be tracked via issues
labeled `phase-9-byos`.

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
