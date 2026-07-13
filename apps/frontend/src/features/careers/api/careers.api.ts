import { getActiveStorageAdapter } from "@/features/storage/adapters/registry";
import type { RecommendationResult, UserProfile, ProfileUpdate } from "../types";

/**
 * Recommendations and profile CRUD delegate to the active storage
 * adapter (see features/storage) so behavior automatically follows the
 * user's chosen storage provider. Default provider is "platform", so
 * existing behavior is unchanged unless the user opts into local-device
 * storage in Settings.
 */
export const careersApi = {
  async getRecommendations(topK = 10): Promise<RecommendationResult> {
    const adapter = getActiveStorageAdapter();
    return adapter.getRecommendations(topK);
  },
};

export const profileApi = {
  async getProfile(): Promise<UserProfile | null> {
    const adapter = getActiveStorageAdapter();
    return adapter.getProfile();
  },

  async updateProfile(updates: ProfileUpdate): Promise<UserProfile> {
    const adapter = getActiveStorageAdapter();
    return adapter.saveProfile(updates);
  },
};
