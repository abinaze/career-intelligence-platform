import type { StorageAdapter, StorageProviderId } from "../types";
import { GoogleDriveAdapter } from "./GoogleDriveAdapter";
import { LocalDeviceAdapter } from "./LocalDeviceAdapter";
import { OneDriveAdapter } from "./OneDriveAdapter";
import { PlatformAdapter } from "./PlatformAdapter";
import { useStorageProviderStore } from "../store/storage.store";

const platformAdapter = new PlatformAdapter();
const localDeviceAdapter = new LocalDeviceAdapter();
const googleDriveAdapter = new GoogleDriveAdapter();
const oneDriveAdapter = new OneDriveAdapter();

/**
 * Resolve a StorageAdapter instance for a given provider ID.
 * Providers without a functional adapter yet (dropbox, local_folder)
 * fall back to the platform adapter — the UI layer prevents selecting
 * them until their Phase 9c/9d work lands.
 */
function resolveAdapter(providerId: StorageProviderId): StorageAdapter {
  switch (providerId) {
    case "local_device":
      return localDeviceAdapter;
    case "google_drive":
      return googleDriveAdapter;
    case "onedrive":
      return oneDriveAdapter;
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
  return resolveAdapter(provider);
}
