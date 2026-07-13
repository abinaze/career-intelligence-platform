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
export function useStorageProvider() {
  const provider = useStorageProviderStore((s) => s.provider);
  const setProvider = useStorageProviderStore((s) => s.setProvider);

  const meta = STORAGE_PROVIDERS.find((p) => p.id === provider) ?? FALLBACK_PROVIDER_META;
  const adapter = getActiveStorageAdapter();

  function selectProvider(next: StorageProviderId): void {
    const nextMeta = STORAGE_PROVIDERS.find((p) => p.id === next);
    if (!nextMeta || nextMeta.availability !== "available") return;
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
