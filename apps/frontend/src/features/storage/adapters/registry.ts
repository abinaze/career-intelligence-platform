import type { StorageAdapter, StorageProviderId } from "../types";
import { DropboxAdapter } from "./DropboxAdapter";
import { GoogleDriveAdapter } from "./GoogleDriveAdapter";
import { LocalDeviceAdapter } from "./LocalDeviceAdapter";
import { OneDriveAdapter } from "./OneDriveAdapter";
import { PlatformAdapter } from "./PlatformAdapter";
import { useStorageProviderStore } from "../store/storage.store";

const platformAdapter = new PlatformAdapter();
const localDeviceAdapter = new LocalDeviceAdapter();
const googleDriveAdapter = new GoogleDriveAdapter();
const oneDriveAdapter = new OneDriveAdapter();
const dropboxAdapter = new DropboxAdapter();

/**
 * Resolve a StorageAdapter instance for a given provider ID.
 * Providers without a functional adapter yet (local_folder) fall back
 * to the platform adapter — the UI layer prevents selecting them until
 * their Phase 9d work lands.
 */
/**
 * Resolve a StorageAdapter instance for a given provider ID.
 * Providers without a functional adapter yet (local_folder) fall back
 * to the platform adapter — the UI layer prevents selecting them until
 * their Phase 9d work lands.
 *
 * Exported (not just used internally by getActiveStorageAdapter) so
 * migration code can resolve the *target* adapter for a provider switch
 * before the switch itself happens — see
 * features/storage/lib/migrateProviderData.ts.
 */
export function getStorageAdapterFor(providerId: StorageProviderId): StorageAdapter {
  switch (providerId) {
    case "local_device":
      return localDeviceAdapter;
    case "google_drive":
      return googleDriveAdapter;
    case "onedrive":
      return oneDriveAdapter;
    case "dropbox":
      return dropboxAdapter;
    case "platform":
    default:
      return platformAdapter;
  }
}

/**
 * Get the currently active storage adapter.
 *
 * Safe to call from plain TypeScript modules (e.g. API client files)
 * as well as React components/hooks — reads the Zustand store's state
 * directly via getState() rather than requiring the useStore() hook.
 */
export function getActiveStorageAdapter(): StorageAdapter {
  const { provider } = useStorageProviderStore.getState();
  return getStorageAdapterFor(provider);
}
