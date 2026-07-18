import { idbDelete, idbGet, idbSet } from "./indexedDb";
import type { OneDriveTokenResponse } from "../api/oneDriveOAuth.api";

/**
 * OneDrive token storage. Same pattern as googleDriveTokens.ts — the same
 * IndexedDB store, under its own distinct key.
 */

const TOKENS_KEY = "onedrive_tokens";

export interface StoredOneDriveTokens {
  access_token: string;
  refresh_token: string | null;
  expires_at: string; // ISO 8601
  scope: string;
}

export async function getOneDriveTokens(): Promise<StoredOneDriveTokens | null> {
  return idbGet<StoredOneDriveTokens>(TOKENS_KEY);
}

export async function setOneDriveTokens(tokens: OneDriveTokenResponse): Promise<void> {
  // Microsoft always rotates the refresh token on use, unlike Google, so
  // this fallback matters less here — kept for defensive symmetry in
  // case a future response shape ever omits it.
  const existing = await getOneDriveTokens();
  const stored: StoredOneDriveTokens = {
    access_token: tokens.access_token,
    refresh_token: tokens.refresh_token ?? existing?.refresh_token ?? null,
    expires_at: tokens.expires_at,
    scope: tokens.scope,
  };
  await idbSet(TOKENS_KEY, stored);
}

export async function clearOneDriveTokens(): Promise<void> {
  await idbDelete(TOKENS_KEY);
}

export async function isOneDriveConnected(): Promise<boolean> {
  return (await getOneDriveTokens()) !== null;
}
