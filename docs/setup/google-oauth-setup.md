# Google OAuth setup (BYOS Google Drive storage)

This walks through creating the Google OAuth credentials the backend's
Google Drive broker needs (see
[`docs/architecture/byos.md`](../architecture/byos.md) for how the flow
works, and [`docs/api/reference.md`](../api/reference.md) for the
endpoints). You can do this before or after deploying — the feature fails
gracefully (503 on the affected endpoints) with no credentials configured.

## 1. Create a Google Cloud project (or reuse one)

1. Go to [console.cloud.google.com](https://console.cloud.google.com/).
2. Create a new project, or select an existing one, from the project
   picker at the top of the page.

## 2. Enable the Drive API

1. **APIs & Services → Library**.
2. Search for **Google Drive API** and click **Enable**.

The app only ever requests the `drive.appdata` scope (a hidden,
per-app storage space — see `docs/architecture/byos.md` for why), so no
other Google APIs need enabling.

## 3. Configure the OAuth consent screen

1. **APIs & Services → OAuth consent screen**.
2. User type: **External** (unless you're on a Google Workspace domain
   and want to restrict this to your organization, in which case
   **Internal** works too and skips verification entirely).
3. Fill in the required fields (app name, support email, developer
   contact email). The app logo and other optional fields aren't needed
   for this scope.
4. **Scopes**: add `https://www.googleapis.com/auth/drive.appdata`. It
   won't appear in the default picker — use **Add or Remove Scopes** and
   paste it into the manual entry field, or search "See, create, and
   delete its own configuration data in your Google Drive."
5. **Test users** (if you leave the app in "Testing" status rather than
   publishing it): add the Google account(s) you'll test with. Apps in
   Testing status only work for accounts explicitly listed here.

Since `drive.appdata` is a narrow, non-sensitive scope, Google's
verification review is usually not required to move out of Testing — but
you don't need to publish at all for local development or a small user
base; Testing status is fine indefinitely, it just caps you at 100 test
users and shows an "unverified app" warning during consent (expected, not
an error).

## 4. Create OAuth 2.0 credentials

1. **APIs & Services → Credentials → Create Credentials → OAuth client ID**.
2. Application type: **Web application**.
3. **Authorized redirect URIs** — add the exact callback URL the backend
   will use. This must match `GOOGLE_OAUTH_REDIRECT_URI` byte-for-byte:
   - Local development: `http://localhost:8000/api/v1/storage/google-drive/callback`
   - Production: `https://<your-api-domain>/api/v1/storage/google-drive/callback`
4. Click **Create**. Copy the **Client ID** and **Client Secret** shown —
   the secret is only displayed once (you can regenerate it later from
   the Credentials page if you lose it).

## 5. Configure the backend

Add to `apps/backend/.env` (or your deployment's environment/secrets
manager):

```bash
GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-client-secret
GOOGLE_OAUTH_REDIRECT_URI=http://localhost:8000/api/v1/storage/google-drive/callback
FRONTEND_URL=http://localhost:3000
```

`FRONTEND_URL` is what the backend redirects the browser back to after
Google's callback — make sure it points at wherever the frontend is
actually served from (no trailing slash).

`GOOGLE_DRIVE_SCOPES`, `GOOGLE_DRIVE_TICKET_TTL_SECONDS`, and
`GOOGLE_DRIVE_EXCHANGE_TTL_SECONDS` all have sensible defaults in
`src/core/config/settings.py` — only override them if you have a specific
reason to.

Redis must also be reachable (`REDIS_URL`) — it's what stages the
short-lived OAuth ticket/exchange secrets. If you're running
`docker-compose.dev.yml`'s `full` profile, Redis is already included.

## 6. Verify it's wired up

With the backend running:

```bash
curl http://localhost:8000/health
```

`google_drive_storage` should read `"enabled"` (it reads `"disabled"` if
`GOOGLE_CLIENT_ID`/`GOOGLE_CLIENT_SECRET` aren't set) and `redis` should
read `"ok"`.

Then, signed into the app, go to **Settings → Storage** and click
**Connect Google Drive**. You should land on Google's consent screen,
approve access, and land back on Settings with a "Connected" badge.

## Troubleshooting

- **`redirect_uri_mismatch` from Google** — the URI in step 3 must match
  `GOOGLE_OAUTH_REDIRECT_URI` exactly, including the scheme (`http` vs
  `https`), port, and trailing slash (there shouldn't be one).
- **"This app isn't verified" warning during consent** — expected while
  the app is in Testing status (see step 3). Click **Advanced → Go to
  (app name) (unsafe)** to proceed; this is normal for apps that haven't
  gone through Google's verification review, not a sign of misconfiguration.
- **`google_drive_storage: "disabled"` on `/health`** — `GOOGLE_CLIENT_ID`
  or `GOOGLE_CLIENT_SECRET` isn't set in the backend's environment.
- **Stuck on "Checking Google Drive status…" in Settings** — check the
  browser console/network tab; this usually means the frontend can't
  reach the backend at all (check `NEXT_PUBLIC_API_URL`), not an OAuth
  problem specifically.
- **Connected, but recommendations/assessment fail afterward** — Drive
  storage still calls the backend's stateless compute endpoints
  (`/stateless/*`) for scoring and ranking; only persistence is
  client-side. If those fail, it's unrelated to the OAuth setup above.

## A note on verification

This guide was written without access to real Google OAuth credentials or
a live redirect target — the backend broker was verified against mocked
HTTP calls to Google (see the PR that shipped it), and the frontend
against a real `next build`/`tsc`/`eslint` pass, but neither was
smoke-tested against Google's actual servers. If anything above turns out
to be inaccurate once you've gone through it for real, it's worth fixing
in this file rather than assuming it's user error.
