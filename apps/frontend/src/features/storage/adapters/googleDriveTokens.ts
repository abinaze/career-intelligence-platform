import { idbDelete, idbGet, idbSet } from "./indexedDb";
import type { GoogleDriveTokenResponse } from "../api/googleDriveOAuth.api";

/**
 * Google Drive token storage.
 *
 * Uses the same IndexedDB store as LocalDeviceAdapter (`cip_local_storage`
 * / `kv`), under its own key, so no new browser storage mechanism is
 * introduced. The backend never sees or stores these tokens after the
 * initial exchange — see docs/architecture/byos.md.
 */

const TOKENS_KEY = "google_drive_tokens";

export interface StoredGoogleDriveTokens {
  access_token: string;
  refresh_token: string | null;
  expires_at: string; // ISO 8601
  scope: string;
}

export async function getGoogleDriveTokens(): Promise<StoredGoogleDriveTokens | null> {
  return idbGet<StoredGoogleDriveTokens>(TOKENS_KEY);
}

export async function setGoogleDriveTokens(tokens: GoogleDriveTokenResponse): Promise<void> {
  // Google doesn't always rotate the refresh token on /refresh — if the
  // response omits it, keep whatever refresh token is already stored
  // rather than overwriting it with null.
  const existing = await getGoogleDriveTokens();
  const stored: StoredGoogleDriveTokens = {
    access_token: tokens.access_token,
    refresh_token: tokens.refresh_token ?? existing?.refresh_token ?? null,
    expires_at: tokens.expires_at,
    scope: tokens.scope,
  };
  await idbSet(TOKENS_KEY, stored);
}

export async function clearGoogleDriveTokens(): Promise<void> {
  await idbDelete(TOKENS_KEY);
}

export async function isGoogleDriveConnected(): Promise<boolean> {
  return (await getGoogleDriveTokens()) !== null;
}
