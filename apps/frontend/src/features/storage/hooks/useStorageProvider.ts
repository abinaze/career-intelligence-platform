import { useStorageProviderStore } from "../store/storage.store";
import { getActiveStorageAdapter, getStorageAdapterFor } from "../adapters/registry";
import { migrateStorageData, type MigrationResult } from "../lib/migrateProviderData";
import { STORAGE_PROVIDERS } from "../types";
import type { StorageProviderId } from "../types";

const FALLBACK_PROVIDER_META = STORAGE_PROVIDERS[0]!;

/**
 * React hook for components that need to display or change the active
 * storage provider (e.g. the Settings "Storage" tab). Re-renders when
 * the provider changes, unlike calling getActiveStorageAdapter() directly.
 */
// Providers that require a completed OAuth handshake before they can
// become the active provider — there are no tokens on first selection,
// unlike platform/local_device which can be switched to instantly.
// Add new OAuth-based providers here as they ship (see Dropbox, Phase 9c).
const PROVIDERS_REQUIRING_CONNECT_FLOW = new Set<StorageProviderId>([
  "google_drive",
  "onedrive",
  "dropbox",
]);

export function useStorageProvider() {
  const provider = useStorageProviderStore((s) => s.provider);
  const setProvider = useStorageProviderStore((s) => s.setProvider);

  const meta = STORAGE_PROVIDERS.find((p) => p.id === provider) ?? FALLBACK_PROVIDER_META;
  const adapter = getActiveStorageAdapter();

  /**
   * Switches the active storage provider, migrating the user's existing
   * profile and assessment data from the current provider to the new
   * one first (see migrateProviderData.ts) so switching doesn't strand
   * data on the old provider. Returns the migration outcome so callers
   * can tell the user what actually happened — `null` means the switch
   * itself didn't happen at all (invalid target, or an OAuth provider
   * selected outside its connect flow).
   */
  async function selectProvider(
    next: StorageProviderId,
    opts?: { fromConnectFlow?: boolean },
  ): Promise<MigrationResult | null> {
    const nextMeta = STORAGE_PROVIDERS.find((p) => p.id === next);
    if (!nextMeta || nextMeta.availability !== "available") return null;

    // See PROVIDERS_REQUIRING_CONNECT_FLOW above. GoogleDriveConnect.tsx /
    // OneDriveConnect.tsx / DropboxConnect.tsx complete the OAuth
    // handshake and then call this with fromConnectFlow: true once
    // tokens actually exist. A plain picker click on one of these
    // providers is a no-op; see StorageOnboarding.tsx.
    if (PROVIDERS_REQUIRING_CONNECT_FLOW.has(next) && !opts?.fromConnectFlow) return null;

    if (next === provider) {
      return { attempted: false, profileRestored: false, assessmentRestored: false };
    }

    const fromAdapter = adapter;
    const toAdapter = getStorageAdapterFor(next);
    const migration = await migrateStorageData(fromAdapter, toAdapter);

    setProvider(next);
    return migration;
  }

  return {
    provider,
    providerMeta: meta,
    adapter,
    providers: STORAGE_PROVIDERS,
    selectProvider,
  };
}
