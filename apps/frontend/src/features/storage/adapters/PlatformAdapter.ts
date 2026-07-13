import { apiClient } from "@/lib/api/client";
import type { StartAssessmentResponse } from "@/features/assessment/types";
import type { ProfileUpdate, RecommendationResult, UserProfile } from "@/features/careers/types";
import { mapRawQuestion, type RawBackendQuestion } from "../api/stateless.api";
import type { LocalAssessmentResults, StorageAdapter } from "../types";

/**
 * Default storage adapter — delegates to the existing platform-hosted
 * (PostgreSQL-backed) endpoints. Calling code that never changes its
 * storage provider sees identical behavior to before this feature existed.
 *
 * Deliberately calls apiClient directly rather than the feature-level
 * api modules (assessmentApi, careersApi, profileApi) to avoid a circular
 * dependency — those modules delegate to the active adapter, which would
 * otherwise call back into them. stateless.api.ts is a leaf module (no
 * dependency on this adapter), so importing its question mapper is safe.
 */
export class PlatformAdapter implements StorageAdapter {
  readonly providerId = "platform" as const;

  async getProfile(): Promise<UserProfile | null> {
    const response = await apiClient.get<UserProfile>("/profile");
    return response.data;
  }

  async saveProfile(updates: ProfileUpdate): Promise<UserProfile> {
    const response = await apiClient.patch<UserProfile>("/profile", updates);
    return response.data;
  }

  async startAssessment(assessmentType = "full"): Promise<StartAssessmentResponse> {
    const response = await apiClient.post<{
      session_id: string;
      assessment_type: string;
      status: string;
      started_at: string;
      questions: RawBackendQuestion[];
    }>("/assessment/start", { assessment_type: assessmentType });

    const data = response.data;
    const questions = data.questions.map(mapRawQuestion);

    return {
      session: {
        id: data.session_id,
        user_id: "",
        assessment_type: data.assessment_type,
        status: data.status as "in_progress",
        started_at: data.started_at,
        completed_at: null,
      },
      questions,
      total_questions: questions.length,
    };
  }

  async submitAssessment(
    sessionId: string,
    responses: Record<string, number>,
  ): Promise<{ session: unknown; results: LocalAssessmentResults }> {
    const response = await apiClient.post<{
      session_id: string;
      model_version: string;
      completed_at: string;
      dimension_scores: LocalAssessmentResults["dimension_scores"];
    }>("/assessment/submit", { session_id: sessionId, responses });

    const data = response.data;
    return {
      session: { id: data.session_id, status: "completed" },
      results: {
        session_id: data.session_id,
        assessment_type: "full",
        completed_at: data.completed_at,
        dimension_scores: data.dimension_scores,
        model_version: data.model_version,
      },
    };
  }

  async getLatestAssessmentResults(): Promise<LocalAssessmentResults | null> {
    try {
      const response = await apiClient.get<LocalAssessmentResults>("/assessment/latest");
      return response.data;
    } catch {
      // Known limitation: no GET /assessment/latest endpoint exists on the
      // backend yet (tracked separately from BYOS work). This mirrors the
      // pre-existing frontend behavior rather than silently changing it.
      return null;
    }
  }

  async getRecommendations(topK = 10): Promise<RecommendationResult> {
    const response = await apiClient.get<RecommendationResult>(
      `/careers/recommendations?top_k=${topK}`,
    );
    return response.data;
  }

  clearAll(): Promise<void> {
    // Not applicable to platform storage — managed via account deletion
    // in Settings, not a local "clear" action.
    return Promise.resolve();
  }
}
