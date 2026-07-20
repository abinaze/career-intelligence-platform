import { idbDelete, idbGet, idbSet } from "./indexedDb";
import type { DropboxTokenResponse } from "../api/dropboxOAuth.api";

/**
 * Dropbox token storage. Same pattern as googleDriveTokens.ts/
 * oneDriveTokens.ts — the same IndexedDB store, under its own key.
 */

const TOKENS_KEY = "dropbox_tokens";

export interface StoredDropboxTokens {
  access_token: string;
  refresh_token: string | null;
  expires_at: string; // ISO 8601
  scope: string;
}

export async function getDropboxTokens(): Promise<StoredDropboxTokens | null> {
  return idbGet<StoredDropboxTokens>(TOKENS_KEY);
}

export async function setDropboxTokens(tokens: DropboxTokenResponse): Promise<void> {
  // Dropbox doesn't rotate the refresh token on /refresh, so this
  // fallback rarely triggers in practice — kept for defensive symmetry
  // with the other two adapters' token helpers.
  const existing = await getDropboxTokens();
  const stored: StoredDropboxTokens = {
    access_token: tokens.access_token,
    refresh_token: tokens.refresh_token ?? existing?.refresh_token ?? null,
    expires_at: tokens.expires_at,
    scope: tokens.scope,
  };
  await idbSet(TOKENS_KEY, stored);
}

export async function clearDropboxTokens(): Promise<void> {
  await idbDelete(TOKENS_KEY);
}

export async function isDropboxConnected(): Promise<boolean> {
  return (await getDropboxTokens()) !== null;
}
