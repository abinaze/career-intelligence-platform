# Dropbox app setup (BYOS Dropbox storage)

Mirrors [`docs/setup/google-oauth-setup.md`](./google-oauth-setup.md) and
[`docs/setup/microsoft-oauth-setup.md`](./microsoft-oauth-setup.md) for
Dropbox. See [`docs/architecture/byos.md`](../architecture/byos.md) for
how the flow works, and [`docs/api/reference.md`](../api/reference.md)
for the endpoints.

## 1. Create a Dropbox app

1. Go to the [Dropbox App Console](https://www.dropbox.com/developers/apps).
2. **Create app**.
3. **Choose an API**: Scoped access.
4. **Choose the type of access you need**: **App folder** — this is what
   sandboxes the app to its own `Apps/<AppName>` folder inside the user's
   Dropbox, so it never sees or touches anything else in their account.
   This is configured here, at app creation, not requested via an OAuth
   scope the way Google's `drive.appdata` or Microsoft's
   `Files.ReadWrite.AppFolder` are.
5. Name the app (must be unique across all of Dropbox — you may need to
   try a few names).

## 2. Configure permissions

1. In the app's **Permissions** tab, enable:
   - `files.content.write`
   - `files.content.read`
2. Click **Submit** to save.

## 3. Add the redirect URI

1. In the app's **Settings** tab, under **OAuth 2 → Redirect URIs**, add:
   - Local development: `http://localhost:8000/api/v1/storage/dropbox/callback`
   - Production: `https://<your-api-domain>/api/v1/storage/dropbox/callback`

## 4. Note your app key and secret

Still on the **Settings** tab: copy the **App key** and **App secret**
(click **Show** to reveal the secret).

## 5. Configure the backend

Add to `apps/backend/.env`:

```bash
DROPBOX_CLIENT_ID=your-app-key
DROPBOX_CLIENT_SECRET=your-app-secret
DROPBOX_OAUTH_REDIRECT_URI=http://localhost:8000/api/v1/storage/dropbox/callback
```

`FRONTEND_URL` and Redis are shared with the other two providers' setup —
see the Google Drive guide if you haven't configured them yet.

## 6. Verify it's wired up

```bash
curl http://localhost:8000/health
```

`dropbox_storage` should read `"enabled"`.

Then, signed into the app, go to **Settings → Storage** and click
**Connect Dropbox**. You should land on Dropbox's consent screen, approve
access, and land back on Settings with a "Connected" badge.

## Disconnecting

Unlike OneDrive, Dropbox has a real revoke endpoint — clicking
**Disconnect** actually revokes the token at Dropbox's end (best-effort;
your locally-stored tokens are cleared either way, even if the revoke
call itself fails). No manual step needed on Dropbox's side afterward.

## Troubleshooting

- **`redirect_uri_mismatch`** — the URI in step 3 must match
  `DROPBOX_OAUTH_REDIRECT_URI` exactly.
- **`dropbox_storage: "disabled"` on `/health`** — `DROPBOX_CLIENT_ID` or
  `DROPBOX_CLIENT_SECRET` isn't set.
- **Connect succeeds but reads/writes fail afterward** — double-check the
  app's **Permissions** tab has both `files.content.write` and
  `files.content.read` enabled and submitted; permission changes only
  take effect for *new* authorizations, so an already-connected user may
  need to disconnect and reconnect after you add a permission.
- **App name rejected at creation** — Dropbox app names must be globally
  unique; try a more specific name if the one you want is taken.

## A note on verification

Same caveat as the other two setup guides: written and the code path
tested against mocked HTTP calls and a real `next build`/`tsc`/`eslint`
pass, but not against Dropbox's actual servers — no live credentials were
available while building this. Treat the first real run through this
guide as the actual test.
