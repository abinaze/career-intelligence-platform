import { apiClient } from "@/lib/api/client";
import type {
  RecommendationResult,
  UserProfile,
  ProfileUpdate,
} from "../types";

/**
 * Career recommendations API.
 */
export const careersApi = {
  /**
   * Fetch personalised career recommendations for the authenticated user.
   * Requires a completed assessment — throws HTTP 400 if none exists.
   */
  async getRecommendations(topK = 10): Promise<RecommendationResult> {
    const response = await apiClient.get<RecommendationResult>(
      `/careers/recommendations?top_k=${topK}`,
    );
    return response.data;
  },
};

/**
 * User profile API.
 */
export const profileApi = {
  /**
   * Fetch or auto-create the authenticated user's profile.
   */
  async getProfile(): Promise<UserProfile> {
    const response = await apiClient.get<UserProfile>("/profile");
    return response.data;
  },

  /**
   * Partially update profile fields. Omitted fields are unchanged.
   */
  async updateProfile(updates: ProfileUpdate): Promise<UserProfile> {
    const response = await apiClient.patch<UserProfile>("/profile", updates);
    return response.data;
  },
};
