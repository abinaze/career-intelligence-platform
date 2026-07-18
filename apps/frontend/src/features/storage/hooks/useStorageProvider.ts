import { useStorageProviderStore } from "../store/storage.store";
import { getActiveStorageAdapter } from "../adapters/registry";
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
const PROVIDERS_REQUIRING_CONNECT_FLOW = new Set<StorageProviderId>(["google_drive", "onedrive"]);

export function useStorageProvider() {
  const provider = useStorageProviderStore((s) => s.provider);
  const setProvider = useStorageProviderStore((s) => s.setProvider);

  const meta = STORAGE_PROVIDERS.find((p) => p.id === provider) ?? FALLBACK_PROVIDER_META;
  const adapter = getActiveStorageAdapter();

  function selectProvider(next: StorageProviderId, opts?: { fromConnectFlow?: boolean }): void {
    const nextMeta = STORAGE_PROVIDERS.find((p) => p.id === next);
    if (!nextMeta || nextMeta.availability !== "available") return;

    // See PROVIDERS_REQUIRING_CONNECT_FLOW above. GoogleDriveConnect.tsx /
    // OneDriveConnect.tsx complete the OAuth handshake and then call this
    // with fromConnectFlow: true once tokens actually exist. A plain
    // picker click on one of these providers is a no-op; see
    // StorageOnboarding.tsx.
    if (PROVIDERS_REQUIRING_CONNECT_FLOW.has(next) && !opts?.fromConnectFlow) return;

    setProvider(next);
  }

  return {
    provider,
    providerMeta: meta,
    adapter,
    providers: STORAGE_PROVIDERS,
    selectProvider,
  };
}
