# Microsoft OAuth setup (BYOS OneDrive storage)

Mirrors [`docs/setup/google-oauth-setup.md`](./google-oauth-setup.md) for
OneDrive. See [`docs/architecture/byos.md`](../architecture/byos.md) for
how the flow works, and [`docs/api/reference.md`](../api/reference.md)
for the endpoints — note there's no disconnect endpoint for OneDrive
(explained below and in both of those docs).

## 1. Register an app in Azure

1. Go to [entra.microsoft.com](https://entra.microsoft.com/) (Microsoft
   Entra admin center — this is where app registrations for both
   personal Microsoft accounts and work/school accounts live).
2. **Applications → App registrations → New registration**.
3. Name it anything (e.g. "Career Intelligence Platform").
4. **Supported account types**: choose **Accounts in any organizational
   directory and personal Microsoft accounts** — this matches the
   default `MICROSOFT_OAUTH_TENANT=common` setting. If you only want to
   support personal Microsoft accounts, choose **Personal Microsoft
   accounts only** and set `MICROSOFT_OAUTH_TENANT=consumers`.
5. **Redirect URI**: platform **Web**, value:
   - Local development: `http://localhost:8000/api/v1/storage/onedrive/callback`
   - Production: `https://<your-api-domain>/api/v1/storage/onedrive/callback`
6. Click **Register**.

## 2. Add the API permission

1. In your new app registration: **API permissions → Add a permission**.
2. **Microsoft Graph → Delegated permissions**.
3. Search for and add **Files.ReadWrite.AppFolder**.
4. Also make sure **offline_access** is present (it's usually added by
   default when you request any delegated permission, since it's how the
   app gets a refresh token — check under the same list; add it
   explicitly if it isn't there).
5. You do **not** need admin consent for `Files.ReadWrite.AppFolder` — it's
   a per-user consent permission, not tenant-wide.

## 3. Create a client secret

1. **Certificates & secrets → Client secrets → New client secret**.
2. Give it a description and an expiry (Microsoft caps this at 24 months
   — you'll need to rotate it before then).
3. Copy the secret's **value** immediately — like Google, it's only shown
   once.

## 4. Note your Application (client) ID

On the app registration's **Overview** page: copy the **Application
(client) ID**.

## 5. Configure the backend

Add to `apps/backend/.env`:

```bash
MICROSOFT_CLIENT_ID=your-application-client-id
MICROSOFT_CLIENT_SECRET=your-client-secret-value
MICROSOFT_OAUTH_REDIRECT_URI=http://localhost:8000/api/v1/storage/onedrive/callback
MICROSOFT_OAUTH_TENANT=common
```

`FRONTEND_URL` and Redis are shared with the Google Drive setup — see
that guide if you haven't configured them yet.

## 6. Verify it's wired up

```bash
curl http://localhost:8000/health
```

`onedrive_storage` should read `"enabled"`.

Then, signed into the app, go to **Settings → Storage** and click
**Connect OneDrive**. You should land on Microsoft's consent screen,
approve access, and land back on Settings with a "Connected" badge.

## An important difference from Google Drive: disconnecting

Clicking **Disconnect** in the app clears your locally-stored tokens and
stops the app from calling OneDrive — it does **not** revoke the grant at
Microsoft's end, because there's no simple API for that in this flow (see
`docs/architecture/byos.md`). If you want to fully revoke this app's
access to your Microsoft account, do it directly from
[account.live.com/consent/manage](https://account.live.com/consent/manage)
(personal accounts) or your organization's Azure AD app access page
(work/school accounts). This is a real platform limitation, not a bug in
this app — worth telling users if this comes up in support.

## Troubleshooting

- **`AADSTS50011: redirect URI mismatch`** — the URI in step 1.5 must
  match `MICROSOFT_OAUTH_REDIRECT_URI` exactly.
- **`AADSTS65001: user or admin has not consented`** — shouldn't happen
  for `Files.ReadWrite.AppFolder` since it's user-consentable, but if your
  organization has tenant-wide consent restrictions turned on, an admin
  may need to approve the app first.
- **`onedrive_storage: "disabled"` on `/health`** — `MICROSOFT_CLIENT_ID`
  or `MICROSOFT_CLIENT_SECRET` isn't set.
- **Works for personal accounts, fails for work/school (or vice versa)**
  — check `MICROSOFT_OAUTH_TENANT` matches what you chose in step 1.4.

## A note on verification

Same caveat as the Google Drive guide: written and the code path tested
against mocked HTTP calls and a real `next build`/`tsc`/`eslint` pass, but
not against Microsoft's actual servers — no live credentials were
available while building this. Treat the first real run through this
guide as the actual test.
