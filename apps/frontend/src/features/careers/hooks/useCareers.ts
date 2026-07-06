import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { careersApi, profileApi } from "../api/careers.api";
import type { ProfileUpdate } from "../types";

export const CAREERS_KEYS = {
  all: ["careers"] as const,
  recommendations: (topK: number) =>
    [...CAREERS_KEYS.all, "recommendations", topK] as const,
};

export const PROFILE_KEYS = {
  all: ["profile"] as const,
  detail: () => [...PROFILE_KEYS.all, "detail"] as const,
};

export function useRecommendations(topK = 10) {
  return useQuery({
    queryKey: CAREERS_KEYS.recommendations(topK),
    queryFn: () => careersApi.getRecommendations(topK),
    staleTime: 10 * 60 * 1000,
    retry: false,
  });
}

export function useProfile() {
  return useQuery({
    queryKey: PROFILE_KEYS.detail(),
    queryFn: () => profileApi.getProfile(),
    staleTime: 5 * 60 * 1000,
  });
}

export function useUpdateProfile() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (updates: ProfileUpdate) => profileApi.updateProfile(updates),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: PROFILE_KEYS.all });
      void queryClient.invalidateQueries({ queryKey: CAREERS_KEYS.all });
    },
  });
}
