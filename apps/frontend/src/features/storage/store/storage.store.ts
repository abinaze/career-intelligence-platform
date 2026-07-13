import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { StorageProviderId } from "../types";

interface StorageProviderState {
  provider: StorageProviderId;
  setProvider: (provider: StorageProviderId) => void;
}

/**
 * Tracks which storage provider the user has chosen.
 *
 * This store persists only the *choice* (a single string) to
 * localStorage — never the user's actual career or psychometric data,
 * which lives in the adapter the choice points to (see registry.ts).
 * Defaults to "platform" so existing users see no behavior change.
 */
export const useStorageProviderStore = create<StorageProviderState>()(
  persist(
    (set) => ({
      provider: "platform",
      setProvider: (provider) => set({ provider }),
    }),
    {
      name: "cip_storage_provider",
    },
  ),
);
