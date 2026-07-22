import { apiClient } from "@/lib/api/client";
import type { StartAssessmentResponse } from "@/features/assessment/types";
import type { ProfileUpdate, RecommendationResult, UserProfile } from "@/features/careers/types";
import { mapRawQuestion, type RawBackendQuestion } from "../api/stateless.api";
import type {
  LocalAssessmentResults,
  RestoreSnapshotResult,
  StorageAdapter,
  StorageSnapshot,
} from "../types";

/**
 * Converts a full UserProfile (as read from some other adapter's
 * exportSnapshot()) into the partial ProfileUpdate shape /profile PATCH
 * expects, dropping null fields rather than sending them — ProfileUpdate's
 * fields are optional-string, not string-or-null, so a null would either
 * fail validation or (worse) silently clear a field the target profile
 * didn't actually have unset.
 */
function profileToUpdate(profile: UserProfile): ProfileUpdate {
  const update: ProfileUpdate = {
    onboarding_step: profile.onboarding_step,
    onboarding_completed: profile.onboarding_completed,
  };
  if (profile.age_range !== null) update.age_range = profile.age_range;
  if (profile.education_level !== null) update.education_level = profile.education_level;
  if (profile.current_field !== null) update.current_field = profile.current_field;
  if (profile.years_of_experience !== null) {
    update.years_of_experience = profile.years_of_experience;
  }
  if (profile.country !== null) update.country = profile.country;
  if (profile.primary_goal !== null) update.primary_goal = profile.primary_goal;
  if (profile.career_concerns !== null) update.career_concerns = profile.career_concerns;
  if (profile.desired_work_environment !== null) {
    update.desired_work_environment = profile.desired_work_environment;
  }
  return update;
}

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

  async exportSnapshot(): Promise<StorageSnapshot> {
    const [profile, assessment] = await Promise.all([
      this.getProfile().catch(() => null),
      this.getLatestAssessmentResults().catch(() => null),
    ]);
    return { profile, assessment };
  }

  /**
   * Restores a profile fully. Cannot restore assessment data: the
   * backend has no endpoint to set a precomputed assessment result
   * directly — only /assessment/start + /assessment/submit, which take
   * raw Likert responses (not retained anywhere, only their computed
   * scores) and always run a fresh scoring pass. So migrating an
   * assessment INTO platform storage isn't possible without a new
   * backend endpoint; the user would need to retake it. This is real
   * and one-directional — migrating OUT of platform storage works fine,
   * since exportSnapshot() above just reads what's already there. See
   * docs/architecture/byos.md.
   */
  async restoreSnapshot(snapshot: StorageSnapshot): Promise<RestoreSnapshotResult> {
    let profileRestored = false;
    if (snapshot.profile) {
      try {
        await this.saveProfile(profileToUpdate(snapshot.profile));
        profileRestored = true;
      } catch {
        profileRestored = false;
      }
    }
    return { profileRestored, assessmentRestored: false };
  }

  clearAll(): Promise<void> {
    // Not applicable to platform storage — managed via account deletion
    // in Settings, not a local "clear" action.
    return Promise.resolve();
  }
}
