import { apiClient } from "@/lib/api/client";
import type { RecommendationResult, UserProfile, ProfileUpdate } from "../types";

export const careersApi = {
  async getRecommendations(topK = 10): Promise<RecommendationResult> {
    const response = await apiClient.get<RecommendationResult>(
      `/careers/recommendations?top_k=${topK}`,
    );
    return response.data;
  },
};

export const profileApi = {
  async getProfile(): Promise<UserProfile> {
    const response = await apiClient.get<UserProfile>("/profile");
    return response.data;
  },

  async updateProfile(updates: ProfileUpdate): Promise<UserProfile> {
    const response = await apiClient.patch<UserProfile>("/profile", updates);
    return response.data;
  },
};
