# Career Intelligence — Desktop-First Transformation Plan

> **Status: planning only. No implementation code in this deliverable.**
> Per the working rule that came with this task ("do not start coding
> immediately... first inspect the actual repository thoroughly... if
> the repository contradicts an architectural assumption, trust the
> repository evidence"), everything below was checked against the real
> uploaded ZIP by reading the actual files, not inferred from the
> product-vision documents that prompted this work. Where the vision
> docs' assumptions turned out to be right, that's noted. Where the
> repo told a different story, the repo wins, and the difference is
> called out explicitly.

---

## Methodology

Every claim below traces to a specific file actually opened during this
audit: `pyproject.toml`, `package.json`, `settings.py`, `main.py`,
`chat_service.py`, `embedder.py`, `faiss_index.py`,
`stateless_service.py`, `load_onet.py`, the four `db/models/*.py`
files, `middleware.ts`, `next.config.ts`, `docker-entrypoint.sh`, and a
repo-wide grep for cookie-setting code. Nothing here is inferred from
the vision documents' own diagrams or assumed from what a typical
FastAPI/Next.js app "usually" looks like.

---

## 1. Current Architecture

**Monorepo:** `apps/frontend` (Next.js 16 App Router, TypeScript
strict) + `apps/backend` (FastAPI, Python 3.12), pnpm/Turborepo +
`uv`. No `app/api` routes exist in the frontend — it's a SPA-style
client calling a separate FastAPI backend via axios, not a Next.js app
with its own server logic. That matters a lot for desktop packaging
(see §4).

**Data layer:** PostgreSQL 16 via `asyncpg` + SQLAlchemy 2.0 async +
Alembic. Redis 7, used *only* for the three BYOS cloud-storage OAuth
brokers' ticket/exchange staging keys (60s–5min TTLs) — never personal
data, confirmed via `settings.py`'s own comments and the earlier BYOS
work in this project.

**AI stack**, and this is good news for a local story:
- Embeddings: `all-MiniLM-L6-v2`, 384-d, via `sentence-transformers`.
  `embedder.py` **already has a deterministic fallback** — if
  `sentence-transformers` fails to import, it silently switches to a
  SHA-256-derived hash vector instead of crashing. This exists today,
  for CI/test environments, not as speculative desktop-readiness — but
  it's exactly the mechanism a "run without torch on a low-end machine"
  mode needs, already built and already exercised.
- Recommendation ranking: FAISS `IndexFlatIP`, in `faiss_index.py`,
  **also already tolerant of `faiss-cpu` being absent** (catches
  `ImportError`, logs a warning, returns empty results rather than
  crashing).
- The current curated O\*NET career catalog (`load_onet.py`) has
  **14 entries.** At that scale FAISS is solving a problem that doesn't
  exist yet — a plain NumPy cosine-similarity loop is instant. This
  matters concretely for the desktop dependency list (§5).
- Chat: a raw `httpx` POST to `https://api.anthropic.com/v1/messages`
  — no Anthropic SDK dependency. `ChatService` builds a personalised
  system prompt server-side from the user's DB-stored profile and
  psychometric scores, then calls the API with the platform's own
  `ANTHROPIC_API_KEY`. Conversation history itself is already
  stateless — the client sends the full history each call; nothing is
  persisted server-side for chat specifically. If `ANTHROPIC_API_KEY`
  isn't set, the service degrades to a clean 503, not a crash — `/health`
  already reports chat as enabled/disabled based on this.

**Auth:** JWT (`PyJWT`) + `passlib[argon2]` password hashing. The
access token is written to `localStorage` (`auth.store.ts`, four call
sites). Separately, `middleware.ts` gates every non-public route by
reading `request.cookies.get("access_token")` and redirecting to
`/login` if it's missing.

**A real, pre-existing bug, found during this audit, unrelated to
anything desktop-specific:** a repo-wide grep for `document.cookie`,
`res.cookie`, `response.set_cookie`, and `Set-Cookie` returns **zero
matches**. Nothing in this codebase ever writes that cookie. The
middleware's gate is checking a value that's never set. Whether this
currently manifests as "logged-in users get redirected to `/login`
anyway" or is masked by something in how Next.js handles client-side
navigation isn't something this audit tested live (no running instance
was available) — but the code, as written, cannot be doing what it
looks like it's doing. This gets fixed as part of the migration
regardless of the desktop question, since the fix is also what desktop
needs (see §4).

**The most useful existing abstraction for this whole effort:**
`src/services/stateless/stateless_service.py` and its
`/api/v1/stateless/*` endpoints. This already computes psychometric
scoring and recommendation ranking **from data supplied directly in
the request, persisting nothing** — it only reads the shared,
non-personal career catalog and FAISS index. It was built to back the
existing BYOS local-device/browser flows. It is, today, already a
zero-persistence compute path for the exact two things ("assess me,
rank careers for me") that matter most for a local desktop story. This
single existing file changes the shape of §6 substantially.

**BYOS storage:** the frontend's `StorageAdapter` interface (5
implementations — Platform, LocalDevice, GoogleDrive, OneDrive,
Dropbox) plus the backend's three OAuth broker services, all following
a documented "never persist tokens" principle (two-secret Redis
ticket/exchange staging, tokens handed to the browser, not the DB).

**Deployment:** currently mid-pivot — Koyeb was tried for real and
didn't work (cause never confirmed); Render is the untried primary
candidate now; Vercel for the frontend; Supabase/Upstash for managed
Postgres/Redis; Oracle VM documented as the better answer once a
credit card is available; a self-hosted `docker-compose.prod.yml` path
also exists. None of this is touched by the plan below — it's the
Cloud mode, staying exactly as-is.

---

## 2. Target Architecture

Three execution modes over one shared core, scoped to what's actually
buildable rather than the full vision-doc matrix:

**Cloud** — today's app, completely unchanged. Everything in the
current Render/Vercel/Supabase pivot stays as-is.

**Fully Local (desktop only)** — a Tauri shell wrapping the existing
Next.js frontend (statically exported, not the current `standalone`
server build) plus a bundled Python process running the *existing*
stateless compute services — psychometric scoring, recommendation
ranking — with **no live relational database at all.** The user's
profile/assessment/recommendation state is stored the same way the
frontend's `LocalDeviceAdapter` already stores browser-local data —
just now backed by a local file instead of IndexedDB. No accounts, no
JWT, no Postgres, no Redis in this mode. This is a materially smaller
lift than "port the ORM to SQLite" — see §6 for why.

**Semi-Local (desktop only, for now)** — same local shell; chat (and
optionally embeddings) routed to a user-supplied API key instead of
the platform's own, stored via the OS credential store, never sent to
Career Intelligence's own servers.

**Mobile — explicitly out of scope for this phase.** This isn't a
vision downgrade, it's the same conclusion the desktop-transformation
brief itself reaches ("do not implement mobile before desktop
architecture is proven"). Concretely: Tauri does ship a mobile shell
for the frontend, but there's no on-device equivalent anywhere in this
plan for the Python compute process — a phone can't run this backend
the way a laptop can. Revisit only after desktop is real, and expect
mobile's "Fully Local" to mean something structurally different (BYO-key/
cloud-only, or a genuinely separate, much smaller on-device pipeline)
rather than a port of the desktop runtime.

---

## 3. Migration Map

| Current location | Action | Target | Reason |
|---|---|---|---|
| `src/services/stateless/*`, `/api/v1/stateless/*` | **Keep** | Core of the local compute path | Already zero-persistence; this is the desktop runtime's backbone, not new code |
| `src/ai/embeddings/embedder.py` | **Keep** | Same | Already degrades gracefully without `torch` |
| `src/ai/recommendation_engine/faiss_index.py` | **Keep, likely bypassed** | Same file kept for Cloud; local build probably skips FAISS entirely | 14-entry catalog doesn't need it; see §5 |
| `src/ai/psychometric_engine/*` | **Keep** | Same | Pure Python/NumPy, no DB or network dependency at all |
| `src/db/models/user.py`, `profile.py` (Postgres `UUID`/`JSON` types) | **Keep, unused locally** | Cloud only | Local mode doesn't touch these tables at all — see §6 |
| `src/services/auth/*`, JWT | **Keep, unused locally** | Cloud only | No accounts in Fully Local mode |
| `src/services/chat/chat_service.py` | **Refactor** | New `LLMProvider` interface: `PlatformAnthropicProvider` (current behavior) + `UserSuppliedKeyProvider` (BYO key, request-scoped, never persisted) | System-prompt-building logic stays server-side either way — it needs the profile/score context regardless of which key sends the request |
| `apps/frontend/src/middleware.ts` | **Replace** | Client-side auth guard reading existing `localStorage`/Zustand state | Confirmed non-functional today (dead cookie check) *and* incompatible with a static Tauri export — one fix addresses both |
| `apps/frontend/next.config.ts` (`output: "standalone"`) | **Refactor** | Build-mode-aware config: `standalone` for Cloud/Vercel, `export` for desktop | The two output modes are mutually exclusive; can't ship one config for both |
| `apps/frontend/src/features/storage/*` (`StorageAdapter`) | **Keep** | Directly reusable | The local Python sidecar becomes, conceptually, a 6th target behind the same interface already proven by `LocalDeviceAdapter` |
| `src/scripts/load_onet.py` | **Refactor** | Split: keep the career definitions + `embed_text` calls; add a release-time build step that writes a portable bundle (flat file + optional index) instead of writing to live Postgres | Local mode needs this data pre-built once by the maintainer, not computed per install |
| `infrastructure/docker/*`, `docs/setup/{render,koyeb,oracle-cloud-vm}-setup.md`, `docs/deployment/guide.md` | **Keep, untouched** | Cloud mode | No reason to touch working, recently-verified deployment docs |
| `CELERY_BROKER_URL` / `CELERY_RESULT_BACKEND` in `settings.py` | **Flag, not acted on** | — | No `celery` package exists in `pyproject.toml`, no worker code beyond an empty `src/workers/__init__.py`. Vestigial, like the Redis-before-BYOS situation noted in this project's earlier history. Don't build around it as if it's real infrastructure. |
| `Settings.HOST = "0.0.0.0"` | **Refactor for local builds** | `127.0.0.1` for the desktop sidecar | The current default is correct for a container; wrong for a process that should only ever talk to its own Tauri shell |

---

## 4. Blocking Issues

Stated plainly, in the order they'd actually bite:

1. **No Python runtime bundling exists anywhere in this project today.**
   Tauri doesn't include one. Freezing the FastAPI backend into a
   single standalone executable per OS (PyInstaller or equivalent) is
   real, unproven work — and the piece most likely to surface an
   unexpected blocker (frozen-binary size once `torch` is in the mix,
   missing native shared libraries on a clean Windows machine,
   antivirus flagging a newly-signed unfamiliar binary). This should be
   spiked *first*, before any UI work, precisely because it's the
   least certain piece.
2. **Postgres-dialect coupling is real but smaller in scope than it
   looks.** `sqlalchemy.dialects.postgresql.UUID`/`.JSON` are used
   directly in `user.py`, `profile.py`, `career.py`. This looked like
   "the whole ORM needs a portability rewrite" until cross-referencing
   against `stateless_service.py` — local mode doesn't need those
   tables at all, so this isn't a blocker for Fully Local, only a
   reminder that Cloud and Local genuinely diverge in what they
   persist (§6 has the full reasoning).
3. **`middleware.ts` is confirmed dead code as route protection today**
   (§1) and separately incompatible with a static Tauri export either
   way. One fix, two reasons to make it.
4. **`next.config.ts`'s `output: "standalone"` and the `export` mode a
   static Tauri build needs are mutually exclusive settings** — this
   needs a build-mode branch, not a shared config file.
5. **No local LLM code exists anywhere in this repo.** "Fully Local
   chat" is not a port of anything — it's new work, with no existing
   fallback pattern to build on the way embeddings and FAISS have.
   Recommendation in §7: don't put it in v1.
6. **Heavy ML dependencies remain a real desktop packaging cost** even
   with the graceful-degradation patterns in place — `torch` alone is
   not small. Mitigated, not eliminated, by making it genuinely
   optional (§5).

---

## 5. Dependency Changes

**Retained everywhere:** `fastapi`, `pydantic`, the psychometric
scoring stack (no heavy deps at all — pure Python/NumPy).

**Retained for Cloud, absent from the desktop build:** `asyncpg`,
`alembic`, `redis`. Local mode has no relational database and no OAuth
broker to stage, so none of these are needed there.

**Made genuinely optional for local builds** — and this is already
half-true today, not a new capability being invented: `torch`,
`transformers`, `sentence-transformers`. A resource-constrained machine
gets the existing deterministic fallback embedder instead of the real
model; this already works, it just isn't currently exposed as a
deliberate user-facing choice.

**Recommend dropping `faiss-cpu` from the local build path
entirely**, not just making it optional. At 14 catalog entries — and
realistically still true even at a few hundred to ~1,000 if the full
O\*NET taxonomy gets loaded eventually — a brute-force NumPy cosine
loop over 384-d vectors is sub-millisecond. `faiss-cpu` is a real
cross-platform packaging cost (compiled native binaries per OS/arch)
for a performance problem that doesn't exist at this data scale. Worth
revisiting only if the catalog ever grows by orders of magnitude
beyond O\*NET's own occupation count.

**New, desktop-only:** an OS credential-store binding. Whether this
lives on the Python side (a `keyring`-style package) or the Tauri/Rust
side (Tauri has store/keyring-adjacent plugins) is a decision for
implementation time, once the sidecar architecture from §4's first
blocking issue is actually proven — not decided speculatively now.

---

## 6. Database Migration Plan

The central finding of this audit: **local mode doesn't need
Postgres-parity, because it doesn't need most of what Postgres is
currently storing.**

The `users` table, JWT auth, and the relational `profile`/`assessment`
schema exist to support multi-user, multi-session Cloud accounts.
Fully Local mode is single-user, single-machine, no-account by design
(matching the original product-vision documents' own "no account with
you" requirement) — and `stateless_service.py` already proves the
*compute* side of this works with zero persistence.

So the actual local persistence need is narrow: the user's own
profile/assessment/recommendation state, stored the same way
`LocalDeviceAdapter` already stores it for the browser today — a local
key-value store, which on desktop becomes a local JSON or SQLite file
under the OS app-data directory, **not** a SQLite port of the existing
Postgres-coupled ORM models. Plus the shared, read-only career catalog
and its (likely FAISS-free, per §5) index, shipped as a static bundle
built once per release by `load_onet.py`'s refactored variant — not
computed per install.

This sidesteps the `UUID`/`JSON` dialect-portability problem almost
entirely: it doesn't need solving for local mode, because the coupled
models simply aren't used there. Cloud mode's schema and driver stay
completely unchanged.

If local mode later needs to keep a history of multiple past
assessments over time (rather than "latest only," which is all
`stateless_service.py` currently implies), that's new, small,
purpose-built local schema work — not a retrofit of the Cloud ORM.

---

## 7. AI/Model Strategy

**Already local today, zero new work required:** psychometric scoring
(pure Python/NumPy) and recommendation ranking (FAISS today, likely
plain NumPy for the local build per §5). This is most of the product's
actual value, and it's already proven not to need a database, an
internet connection, or even `torch`.

**Genuinely new work, but modest:** model-download UX. The embedding
model is the *only* thing that needs downloading for the "real" (non-
fallback) local experience — roughly 80MB for MiniLM, one-time,
already cacheable via the existing `MODEL_CACHE_DIR` setting. Resource
detection can start small: a RAM/disk check gating "use the real model"
vs. "use the existing fallback embedder," not the full GPU/quantization
tier system the vision docs sketch as a v0.6/v0.7 idea — building that
now would be exactly the kind of premature scope the vision docs'
own staged roadmap (and doc 30's explicit instructions) warn against.

**Chat, staged realistically across the three modes:**
- Cloud: unchanged, platform Anthropic key.
- Semi-Local: `UserSuppliedKeyProvider`, BYO key, real but modest new
  work — a provider abstraction plus credential storage, no local
  inference required. This is also the piece worth shipping in the
  *existing web app* first (see §11, step 1) since it needs no
  packaging decisions to be useful.
- Fully Local chat: **recommend not shipping this in v1.** There is no
  existing code to build on here — it's a genuinely separate, larger
  project (bundling something like Ollama or a `llama.cpp` binary,
  managing its own model download and resource story on top of
  everything else). Fully Local v1 should mean "scoring and career
  matching work with zero network and zero account," which is most of
  the value and needs none of this; local chat is a real v2.

---

## 8. Security Plan

- **Credential storage:** OS-native (Windows Credential Manager /
  macOS Keychain / Linux Secret Service), via whichever of a Python
  `keyring` package or a Tauri-side plugin turns out to fit the chosen
  sidecar architecture — decided at implementation time, not
  speculatively now.
- **BYO API keys are never persisted server-side, in any mode** — the
  local Python process is still logically "a server" from the
  frontend's point of view, so it gets the same treatment the existing
  BYOS OAuth brokers already apply to cloud storage tokens: handled
  per-request, never written to disk on the backend side.
- **Update signature verification via Tauri's own signed updater** —
  confirmed current and maintained (stable release v2.10.1, April
  2026), ships real cryptographic signing against a `latest.json`
  manifest. Not something to build from scratch.
- **The local sidecar binds to `127.0.0.1`, not `0.0.0.0`** — a small,
  concrete change from the current `Settings.HOST` default, which is
  correct for a container and wrong for a process that should never be
  reachable from outside its own machine.

---

## 9. Packaging Plan

- **Tauri v2**, confirmed stable and actively maintained. Desktop
  targets (Windows/macOS/Linux) now; mobile shells exist in the same
  framework for whenever that's revisited, per §2.
- **Windows first**, matching the explicit recommendation in the
  product-vision documents — this narrows the packaging surface
  (installer format, code signing, sidecar binary format) to one OS
  before generalizing, rather than solving three packaging problems at
  once.
- **Code signing is a real, recurring line-item, not a one-time task.**
  A Windows code-signing certificate is a paid, renewing purchase.
  Apple Developer Program membership (needed once/if macOS is added)
  is $99/year for an individual account, confirmed current — both
  should be budgeted now rather than discovered as a surprise later,
  since skipping them is exactly what makes an app look like "a
  developer project wrapped in a GUI" instead of real software, per
  the vision docs' own stated concern.
- **The sidecar-freezing spike from §4 is the highest-priority,
  least-proven piece of this entire plan** and should happen before
  any Tauri UI work, not after.

---

## 10. Update Plan

- **Tauri's own updater plugin against versioned GitHub Releases**, not
  a custom-built update server — this is a real, current, maintained
  feature (confirmed v2.10.1), matching exactly what the vision
  documents described, and it already includes cryptographic signature
  verification out of the box.
- **Versioned releases only, never tracking `main` directly** — this
  also matches how this project already operates its Cloud deployment
  pivots (reviewable PRs, not silent main-branch changes), so it's a
  continuation of an existing discipline, not a new one.
- **Data and application binaries stay on separate paths on disk**
  (version directories vs. a stable user-data directory) — standard
  practice, low technical risk, but needs deciding *before* the first
  real installer ships, since retrofitting it after users have data on
  disk in the wrong place is much more painful than deciding it now.

---

## 11. Migration Sequence

The order below front-loads the least-certain, highest-risk pieces —
deliberately not the order a UI-first instinct would pick.

1. **Ship the `LLMProvider` abstraction (Platform + BYO-key) in the
   existing web app first.** This needs no packaging decisions, works
   today, and de-risks the credential-handling design (§8) before
   anything desktop-specific is built on top of it. This was already
   the agreed next step before this transformation plan was written.
2. **Spike: freeze the FastAPI backend into a single standalone
   executable and confirm it actually runs**, starting with Windows,
   *before* writing any Tauri UI code. This is §4's first and biggest
   blocking issue — if it doesn't work cleanly, everything downstream
   changes, so it needs to be answered first, not assumed.
3. **Build the local data bundle**: refactor `load_onet.py` into a
   release-time build step producing a portable career catalog (plus
   index, if FAISS turns out to still be wanted — see §5's case for
   dropping it).
4. **Build the local profile/assessment persistence layer** — flat
   file or SQLite, not a Postgres port — behind the same
   `StorageAdapter`-shaped interface the frontend already uses.
5. **Replace `middleware.ts`** with a client-side auth guard (fixes
   the existing dead-cookie bug either way) and **make
   `next.config.ts` build-mode-aware** (`standalone` for Cloud,
   `export` for desktop).
6. **Wire the Tauri shell** around the statically-exported frontend
   and the frozen sidecar from step 2 — Windows only.
7. **Add Tauri's signed updater** against GitHub Releases.
8. **Only then**, Semi-Local UX polish — provider-connect screens,
   resource detection, first-run flow. Real and valuable, but
   sequenced after the harder architectural risk (steps 2–6) is
   retired, not before it, matching the vision documents' own explicit
   warning against building UX polish before the runtime is proven.

Mobile stays out of this sequence entirely, per §2.

---

## 12. Scope Triage: Offline / Lifecycle / Security / Distribution

A follow-up review of this plan raised 18 additional areas (offline
behavior, installer lifecycle, crash recovery, logging, process
management, resource limits, model lifecycle, backup/restore, version
migration, threat model, code signing, release channels, feature
flags, accessibility, i18n, licensing, supply chain, telemetry) and
closed with the right instinct: *"optimize for the smallest
architecture that can actually be shipped... not theoretical
architecture."* Agreed — so this section triages rather than expands.
Each item gets folded into the existing plan at near-zero cost, or
explicitly parked with a stated reason it's safe to defer, not
silently dropped.

### Fold in now — cheap today, expensive to retrofit later

These attach to steps already in §11's sequence, not new steps.

- **Backup/restore and data export** (item 8) — **don't design a new
  format.** `docs/architecture/byos.md` already defines a versioned
  export envelope (`format_version`, `exported_at`, `exported_from`)
  for the existing BYOS manual export/import feature (Phase 9d). The
  local desktop persistence layer (§11 step 4) should use the exact
  same envelope shape from day one. This turns "add backup/restore" from
  new design work into "point the existing format at a new local file
  instead of a downloaded JSON," and it's the reason to decide this at
  step 4, not bolt it on after the format's already shipped without it.
- **Version migration for local data** (item 9) — direct consequence of
  the point above: because the envelope already carries
  `format_version`, versioned local-schema migration is mostly free if
  step 4 is built with that field from the start. Costs real rework
  if added after the fact.
- **Installer/uninstaller lifecycle** (item 2) — already implied by
  §10's "data and application binaries stay on separate paths," but
  make the rule explicit now: **uninstall removes the app directory
  only, never the data directory**, and "delete all data" is a
  separate, deliberate, confirmed action in-app, not a side effect of
  uninstalling. Cheap to state now; a real support headache if decided
  after people have data on disk.
- **Process management** (item 5) — not a new step, it's what the §11
  step 2 sidecar spike needs to answer anyway (startup, health check,
  port, shutdown). Naming it explicitly here just makes sure the spike
  doesn't stop at "does a frozen binary run" without also answering
  "does the Tauri shell know if it's alive."
- **Threat model, scoped to what's actually being built** (item 10) —
  not an enterprise exercise; three concrete things worth deciding
  alongside the step 2 spike because they're architecture, not
  polish: the sidecar binds `127.0.0.1` only (already in §8), any
  local IPC between Tauri and the sidecar is treated as trusted-local
  (not exposed), and logs never include API keys or full profile/chat
  content — a redaction rule applied at the logging layer, not
  reviewed case-by-case later.
- **Telemetry policy** (item 18) — trivial to state now and worth
  stating before any code exists to leak from: **no telemetry, no
  analytics, by default, matching the current codebase exactly** —
  nothing in this project sends usage data anywhere today. Free to
  decide now, a real privacy-model rewrite if telemetry is added
  later without having decided this first.
- **Offline behavior, as a stated principle** (item 1) — Fully Local
  mode already implies zero network dependency for core features; the
  one rule worth writing down now is that any online-only feature
  (Semi-Local chat, Cloud sync) fails with a specific, honest reason
  shown to the user, never a silent hang or a generic error — this
  shapes the error-handling pattern from the start rather than
  retrofitting good messages later.
- **Code signing** (item 11) — already in §9; no change, just
  confirming it's not missing from this pass.
- **Licensing — a real inconsistency, found while checking this item.**
  `apps/backend/pyproject.toml` declares `license = { text = "MIT" }`.
  The repo's actual `LICENSE` file and README are **PolyForm
  Noncommercial License 1.0.0** — these don't match. Worth fixing the
  stale `pyproject.toml` field regardless of the desktop work. More
  importantly for this plan specifically: PolyForm Noncommercial
  restricts *commercial* use of the software itself — worth deciding
  now, before any packaging work, whether the desktop distribution
  (and any future paid tier) is intended to stay noncommercial or
  needs a different license, since that's a much harder thing to
  change after people have already installed copies under one license
  than to decide up front. This plan takes no position on which —
  it's a business decision, not a technical one — but it needs an
  actual answer before a public download link goes out.

### Explicitly parked — real, but premature before v1 exists

Stated with a reason each, not dropped silently:

- **Crash recovery / safe mode** (item 3) — needs a runtime that can
  actually crash first; premature before §11 step 2 even proves the
  sidecar runs at all.
- **Diagnostics UI** (item 4) — the redaction *rule* is folded in
  above; the actual Diagnostics screen is v2 UX polish, already
  sequenced after the architecture in §11 step 8.
- **Resource limit enforcement** (item 6) — §7 already covers
  *detection*-driven model selection for v1; hard-enforced caps (max
  RAM/CPU/concurrent tasks) are real but not needed until there's more
  than one local model competing for resources.
- **Full model lifecycle** (item 7) — v1 has exactly one downloadable
  model (MiniLM) with a binary install/fallback choice. A full
  discover/verify/register/unload/rollback lifecycle is speculative
  infrastructure until there's a second model to manage.
- **Release channels** (stable/beta/dev, item 12) — nothing to branch
  from until there's a released v1.
- **Feature flags** (item 13) — genuine premature infrastructure for a
  pre-v1, single-developer project.
- **Accessibility polish** (item 14) — real and worth doing well, but
  it's UX polish, already correctly last in §11's sequence (step 8),
  not an architectural decision that gets more expensive if deferred.
- **Internationalization** (item 15) — the source document's own text
  already agrees this isn't urgent; the only cheap thing worth doing
  now is not hard-coding user-facing strings carelessly, which is a
  coding-time habit, not a design decision to make in this plan.
- **Supply-chain SBOM / reproducible builds** (item 17) — genuine
  mature-product tooling; the one piece already true today is that
  `pyproject.toml` and `package.json` both pin dependencies with
  version constraints. A full SBOM/signed-release pipeline is real
  work worth doing once there's a real release to protect, not before
  one exists.

---



No code changes accompany this document. Per the working rule this
task started under, implementation begins only after this plan is
reviewed — and specifically after step 2 above (the sidecar spike)
produces a real answer, since several packaging decisions in §8–§9
genuinely depend on what that spike finds.
