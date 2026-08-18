import { idbDelete, idbGet, idbSet } from "@/features/storage/adapters/indexedDb";

/**
 * Storage for the user's own Anthropic API key (BYO-key chat).
 *
 * Uses the same IndexedDB store as LocalDeviceAdapter and the BYOS
 * cloud-storage tokens (`cip_local_storage` / `kv`), under its own key
 * — no new browser storage mechanism introduced, and deliberately not
 * localStorage (see docs/desktop/TRANSFORMATION_PLAN.md section 8's
 * credential-storage principle: BYO API keys are never persisted
 * server-side, and client-side they follow the same IndexedDB
 * convention already established for OAuth tokens, not localStorage).
 *
 * The key never touches this app's backend at rest — it's attached to
 * individual chat requests as a header (see
 * features/chat/api/chat.api.ts) and used there for exactly one
 * request each time.
 */

const KEY = "ai_provider:anthropic_byo_key";

export async function getAnthropicByoKey(): Promise<string | null> {
  return idbGet<string>(KEY);
}

export async function setAnthropicByoKey(apiKey: string): Promise<void> {
  await idbSet(KEY, apiKey);
}

export async function clearAnthropicByoKey(): Promise<void> {
  await idbDelete(KEY);
}

export async function hasAnthropicByoKey(): Promise<boolean> {
  return (await getAnthropicByoKey()) !== null;
}
