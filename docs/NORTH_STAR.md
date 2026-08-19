# Career Intelligence — North Star

> **Read this file first, before any other planning doc, in any new
> chat session working on this repo.** It exists specifically so the
> project's direction doesn't drift depending on which chat is
> continuing the work. If anything in a chat conversation contradicts
> this file, **this file wins** unless the project owner explicitly
> updates it. `docs/desktop/TRANSFORMATION_PLAN.md` is the detailed
> technical companion to this document — read both, but this one is
> the anchor.

---

## 1. What this project is becoming, in one paragraph

Career Intelligence is pivoting from a hosted web app to a **Windows
desktop application**, distributed as a signed installer via GitHub
Releases, with no required account, no required internet connection,
and no required Career Intelligence backend for its core features
(psychometric assessment, career matching, explanations). A **Semi-
Local** mode lets someone optionally connect their own AI provider key
for chat and other online features. This is not a redesign — it's a
continuation of the BYOS (Bring-Your-Own-Storage) philosophy already
built into this repo, taken to its logical conclusion: bring your own
*compute*, not just your own storage.

## 2. The one decision this file does not make for you

Every other section below assumes an answer to this question, and it
has not been answered yet as of this document's writing:

> **Does the existing hosted Cloud product (Render backend, Postgres,
> the account/JWT system, the BYOS cloud-storage OAuth brokers) stay
> a maintained, parallel product alongside Desktop — or does it get
> archived out of the active codebase once Desktop is real?**

A prior planning pass (see `docs/desktop/TRANSFORMATION_PLAN.md`, written
before this document) assumed Cloud stays untouched indefinitely. A
later planning pass argued the opposite — that Desktop *is* the
product now and Cloud-specific code (auth, JWT, Postgres models/
migrations/repositories, the three OAuth brokers, Render/Koyeb/Oracle
deployment docs and workflows) should move to an `archive/` path or be
deleted outright, since carrying two full product architectures
forward in parallel is real, ongoing maintenance cost for a
single-developer project.

**Both positions are defensible. This document does not pick one.**
The file-by-file plan in §5 is written so either answer is executable
from it — but the actual order of work, and whether Phase 2 involves
deleting real, working code, depends entirely on this answer. Get it
recorded here before Phase 1 finishes:

```
DECISION: [ pending — fill in: "keep both" | "archive cloud" | other ]
DECIDED ON: [ date ]
REASONING: [ one paragraph ]
```

## 3. What both directions already agree on

Regardless of how §2 resolves, the following is settled and safe to
build on immediately:

- **v1's scope is exactly this, no more:**
  - *Fully Local*: profile, psychometric assessment, scoring, career
    matching, explanations, export/import/backup/restore — all with
    zero network dependency.
  - *Semi-Local*: the above, plus optional chat via a user-supplied AI
    provider key (Anthropic today; the `LLMProvider` interface already
    supports adding others without touching call sites).
  - **Explicitly not v1**: mobile, a platform-owned AI key inside the
    desktop app, cloud storage OAuth (Google Drive/OneDrive/Dropbox)
    inside the desktop app, a local LLM, release channels, telemetry,
    a plugin system. Some of these may return post-v1; none block it.
- **The database direction for local mode**: not a SQLite port of the
  Postgres ORM. `services/stateless/stateless_service.py` already
  proves the core compute (scoring, ranking) needs zero persistence —
  local mode persists only the user's own profile/assessment/
  recommendation state (a local file, following the same envelope
  shape `docs/architecture/byos.md` already defines for export/import)
  and a maintainer-built, release-time career data bundle. See
  `docs/desktop/TRANSFORMATION_PLAN.md` §6 for the full reasoning.
- **Drop `faiss-cpu` from the desktop build.** The current O*NET
  catalog has 14 entries. A NumPy cosine loop is instant at this scale
  and removes a compiled, cross-platform-fragile native dependency.
  Revisit only if the catalog grows by orders of magnitude.
- **No platform-owned Anthropic key ships inside the desktop app.**
  Fully Local means fully local — bundling a platform API key would
  mean every install could spend the maintainer's money. Semi-Local
  chat requires the user's own key, full stop.
- **Recommendation quality must stay honest when the real embedding
  model isn't available.** `embedder.py`'s hash-based fallback exists
  for CI, not as an equivalent-quality substitute — recommendations
  computed from it must be visibly labeled as reduced-confidence /
  structured-matching-only in the UI, never silently presented as
  equivalent to real semantic matching. This is a correctness
  requirement, not a UI nice-to-have — see §8.
- **`load_onet.py` runs at release-build time, on the maintainer's
  machine, never on a user's installed copy.** Its output is a
  portable data bundle shipped inside the installer.
- **Cleanup is safe and independent of §2**: empty placeholder
  directories/files (`services/analytics/`, `services/career_ontology/`,
  `workers/`, `api/middleware/` — all currently empty `__init__.py`
  stubs, confirmed against the real repo, not assumed) and redundant
  `.gitkeep` files sitting in directories that already have real
  content get removed regardless of which way §2 resolves.
- **License stays PolyForm Noncommercial 1.0.0.** Already corrected in
  `pyproject.toml` to match the real `LICENSE` file. Do not change this
  without the project owner's explicit say-so, in either direction —
  not to something more permissive, and not without checking bundled
  model/dependency licenses first (see
  `docs/desktop/TRANSFORMATION_PLAN.md` §12 for what's already been
  checked: Tauri, PyInstaller, and the MiniLM model's own licensing
  ambiguity around its training data).

## 4. Execution discipline for every phase

This applies whether a phase is done in this chat or a future one:

1. **One GitHub Issue per phase, written before the work starts.**
   States the problem, the evidence, and the acceptance criteria. The
   phase's PR references and closes it.
2. **Real verification, every time** — the same discipline already
   established in this project: actual `ruff`/`mypy`/`pytest` runs for
   backend changes, actual `tsc`/`eslint`/`prettier`/`next build` for
   frontend changes touching routing, actual YAML validation for
   workflow changes. Never claim a check happened if it didn't.
3. **Many small, real commits over one large one.** Each commit does
   one coherent thing and has a real multi-line message explaining
   what and why, not just what.
4. **A full PR description per phase**: summary, what changed (table),
   design decisions worth knowing about, a verification section that
   states plainly what was and wasn't tested, what's left, and related
   links (back to this file and to the phase's Issue).
5. **This file gets updated, not left stale**, whenever a phase
   changes something §2 or §3 assumed. If a future chat's plan
   contradicts this file, the contradiction gets resolved *in this
   file* — not silently overridden in a chat transcript that the next
   session won't see.

## 5. File-by-file disposition

Grounded against the real repo as of this document's writing (not
inherited from any planning document's assumptions). Four buckets:
**Keep** (used by Desktop, no change in direction needed), **Refactor**
(used by Desktop, but needs real changes first), **Cloud-only**
(needed only if §2 resolves to "keep both" — otherwise archived or
removed), **Empty/vestigial** (safe to remove regardless of §2).

### Keep as-is

```
apps/backend/src/ai/psychometric_engine/          (dimensions, question_bank, scorer)
apps/backend/src/ai/explainability/explainer.py
apps/backend/src/services/stateless/stateless_service.py
apps/backend/src/api/v1/endpoints/stateless.py
apps/backend/src/services/chat/llm_provider.py
apps/backend/src/services/chat/chat_service.py
apps/backend/src/features/aiProviders/*            (frontend)
docs/architecture/byos.md
docs/desktop/TRANSFORMATION_PLAN.md
```

### Refactor (Desktop needs these, but not as they are today)

| File | What's wrong today | What Desktop needs |
|---|---|---|
| `ai/embeddings/embedder.py` | Fallback exists but isn't surfaced to the UI as a quality difference | Same fallback logic; the *caller* needs to label output quality (§3, §8) |
| `ai/recommendation_engine/faiss_index.py`, `ranker.py` | FAISS-oriented; DB-adjacent assumptions | Replace FAISS with NumPy at current catalog scale; decouple from any DB-backed career source |
| `scripts/load_onet.py` | Writes directly to live Postgres | Split: keep the O*NET definitions + embedding calls; add a release-time build step writing a portable bundle |
| `apps/frontend/src/middleware.ts` | Confirmed dead code (gates on a cookie nothing ever sets) *and* Next.js 16 itself deprecates the `middleware` convention in favor of `proxy` *and* incompatible with a static Tauri export — three reasons, one fix | Client-side auth guard, or removed outright if §2 resolves to "no accounts in the active product" |
| `apps/frontend/src/lib/api/client.ts` | Assumes JWT + refresh-token + `/login` redirect lifecycle | Needs a local-runtime-aware client (talks to `127.0.0.1:<port>`, no JWT) if Desktop drops accounts per §2 |
| `apps/backend/src/main.py` (`Settings.HOST`) | Defaults to `0.0.0.0`, correct for containers, wrong for a local sidecar | `127.0.0.1` for the desktop build |
| `apps/backend/pyproject.toml` | One dependency list for every environment | Split into core-local / optional-AI / cloud-only / dev groups so the desktop build doesn't pull `asyncpg`/`redis`/`alembic` at all |

### Cloud-only — disposition depends entirely on §2

If §2 resolves to "archive cloud," everything below moves to an
`archive/cloud/` path (not deleted outright — kept for reference until
Desktop is confirmed stable) or is removed in a deliberate, separate
cleanup phase. If §2 resolves to "keep both," everything below stays
exactly where it is, untouched, and Desktop is additive rather than
replacing it.

```
Backend:
  src/api/v1/endpoints/auth.py
  src/api/v1/dependencies/auth.py
  src/services/auth/auth_service.py
  src/core/security/jwt.py
  src/db/engine.py
  src/db/migrations/
  src/db/models/{base,career,profile,user}.py
  src/db/repositories/{base,career,psychometric,user}.py
  src/services/profile/profile_service.py           (DB-backed profile CRUD — confirmed)
  src/services/psychometric/assessment_service.py    (DB-backed — confirmed)
  src/services/recommendation/recommendation_service.py  (DB+FAISS-backed — confirmed)
  src/api/v1/endpoints/{assessment,profile,careers}.py
  src/api/v1/endpoints/{dropbox_oauth,onedrive_oauth,storage_oauth}.py
  src/services/storage_oauth/*
  src/core/cache/redis_client.py
  src/schemas/requests/auth.py, responses/auth.py
  src/schemas/requests/storage_oauth.py, responses/storage_oauth.py

Frontend:
  src/app/(auth)/*
  src/features/auth/*
  src/features/storage/adapters/{GoogleDriveAdapter,OneDriveAdapter,DropboxAdapter,PlatformAdapter}.ts
  src/features/storage/components/{GoogleDriveConnect,OneDriveConnect,DropboxConnect}.tsx
  src/features/storage/api/{googleDriveOAuth,oneDriveOAuth,dropboxOAuth}.api.ts
  src/features/settings/components/{AccountForm,ChangePasswordForm,DangerZone}.tsx
  src/lib/validations/auth.schemas.ts
  src/types/auth.ts

Infra/docs:
  infrastructure/docker/, infrastructure/nginx/, infrastructure/huggingface/
  .github/workflows/deploy-oracle-vm.yml
  docs/setup/{render,koyeb,oracle-cloud-vm}-setup.md
  docs/deployment/guide.md
  apps/backend/Dockerfile
```

Note what stays **regardless** even in "archive cloud": `StorageAdapter`,
`LocalDeviceAdapter`, `DataExportImport`, `migrateProviderData.ts`, and
`StorageSettings.tsx`'s local-device path — these aren't cloud-specific,
they're the local-storage foundation Desktop builds on directly.

### Empty/vestigial — remove regardless of §2

```
apps/backend/src/services/analytics/__init__.py       (empty)
apps/backend/src/services/career_ontology/__init__.py (empty)
apps/backend/src/workers/__init__.py                   (empty; matches the vestigial
                                                          CELERY_BROKER_URL/RESULT_BACKEND
                                                          settings — no celery dependency
                                                          exists anywhere in pyproject.toml)
apps/backend/src/api/middleware/__init__.py            (confirmed empty, zero bytes)
```

Plus a repo-wide pass removing `.gitkeep` files from directories that
already contain real files (dozens of these exist under
`apps/frontend/src/features/*` and `apps/frontend/src/app/*` — a
`.gitkeep`'s only job is keeping an *empty* directory tracked; once
real files exist there it's inert clutter, not a safety mechanism).
Directories that are still genuinely empty (e.g. `components/charts/`,
`components/shared/`, `components/ui/`, `app/(admin)/admin/`,
`app/(dashboard)/report/`) keep their `.gitkeep` until something real
lands there.

## 6. Phase breakdown

Each phase gets its own Issue, its own PR, and updates this file if it
changes an assumption in §2 or §3.

- **Phase 0 — Repo hygiene** (safe regardless of §2): CodeQL
  `permissions:` findings on `ci.yml`/`deploy-oracle-vm.yml`, empty
  placeholder file removal, redundant `.gitkeep` cleanup, a real look
  at the open Dependabot alerts (transitive npm deps via
  `pnpm-lock.yaml` — `nanoid`, `brace-expansion`, `undici`, `js-yaml`,
  `postcss`, `sharp`; a partial `pnpm.overrides` already exists for
  `postcss`/`form-data`/`js-yaml`/`vite` but the lockfile still shows
  older vulnerable resolutions coexisting for several of these,
  meaning the overrides aren't fully closing the gap — needs its own
  careful pass, not a guess).
- **Phase 1 — §2 decision recorded.** Nothing past this point proceeds
  until the box in §2 is filled in.
- **Phase 2 — depends on §2's answer**: either (a) archive the
  Cloud-only file list above into `archive/cloud/` with a clear README
  explaining what it is and why it's there, or (b) confirmed no-op,
  Desktop work proceeds additively.
- **Phase 3 — Database-free core.** Remove `stateless_service.py`'s
  remaining indirect DB dependency for career data; refactor
  `load_onet.py` into its release-time-bundle form; drop `faiss-cpu`
  from the desktop dependency set in favor of NumPy.
- **Phase 4 — Local data persistence.** The local
  profile/assessment/recommendation file store, using the BYOS export
  envelope shape.
- **Phase 5 — Local runtime / FastAPI sidecar.** `127.0.0.1` binding,
  dependency-set split in `pyproject.toml`, the standalone-executable
  freeze spike (`docs/desktop/TRANSFORMATION_PLAN.md` §4's first
  blocking issue — the least-proven piece of the whole plan).
- **Phase 6 — Frontend switches to the local runtime.** API client
  redesign (if §2 drops accounts), `middleware.ts` replacement,
  `next.config.ts` build-mode split (`standalone` vs `export`).
- **Phase 7 — First-run setup, model manager, provider manager UI.**
- **Phase 8 — Tauri shell, Windows packaging, code signing.**
- **Phase 9 — GitHub Release + signed auto-updater.**
- **Phase 10 — Polish**: diagnostics, crash recovery, accessibility —
  everything `docs/desktop/TRANSFORMATION_PLAN.md` §12 already
  explicitly deferred past v1.

## 7. What already shipped (confirmed merged, this repo)

- BYOS: `StorageAdapter` pattern, Local Device / Google Drive / OneDrive
  / Dropbox adapters, export/import, migration tooling.
- `LLMProvider` abstraction: platform key or user-supplied key for
  chat, request-scoped, never persisted server-side.
- The Render deployment pivot (Koyeb tried and failed for an
  unconfirmed reason; Render is the untested primary candidate; Oracle
  VM documented and gated behind repo secrets that are deliberately
  unset until a credit card is available — the Oracle workflow
  "failing" on every push to `main` is that guard working as designed,
  not a bug).
- This document and `docs/desktop/TRANSFORMATION_PLAN.md`.

## 8. Non-negotiable correctness note

The current recommendation pipeline weights semantic similarity at
roughly half of a career match's score. If the real embedding model
is unavailable and the code silently substitutes the deterministic
hash-based fallback for that same weight, the resulting score is not a
degraded version of the same measurement — it's a different, much
weaker signal wearing the same number. Any Desktop work touching the
recommendation pipeline must make this distinction visible to the user
(e.g., "Standard local model — full recommendations" vs. "Lightweight
mode — reduced semantic matching"), not just to the maintainer reading
the code. This is called out here, separately from §3, because it's
the kind of thing that's easy to quietly regress on during a large
refactor.
