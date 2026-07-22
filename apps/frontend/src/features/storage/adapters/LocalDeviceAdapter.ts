import type { StartAssessmentResponse } from "@/features/assessment/types";
import type { ProfileUpdate, RecommendationResult, UserProfile } from "@/features/careers/types";
import { mapRawQuestion, statelessApi } from "../api/stateless.api";
import type {
  LocalAssessmentResults,
  RestoreSnapshotResult,
  StorageAdapter,
  StorageSnapshot,
} from "../types";
import { idbClearAll, idbGet, idbSet } from "./indexedDb";

const KEYS = {
  profile: "local_profile",
  assessment: "local_assessment_results",
  recommendations: "local_recommendations_cache",
} as const;

// Mirrors ProfileService._compute_completeness on the backend, adapted for
// a plain client-side object rather than an ORM row. Kept in sync manually
// — see docs/architecture/byos.md for why this isn't shared code.
const COMPLETENESS_WEIGHTS: Record<string, number> = {
  education_level: 0.15,
  current_field: 0.15,
  years_of_experience: 0.1,
  country: 0.05,
  primary_goal: 0.2,
  career_concerns: 0.1,
  desired_work_environment: 0.1,
  age_range: 0.05,
  has_assessment: 0.1,
};

function computeLocalCompleteness(profile: Partial<UserProfile>, hasAssessment: boolean): number {
  let score = 0;
  for (const [field, weight] of Object.entries(COMPLETENESS_WEIGHTS)) {
    if (field === "has_assessment") {
      if (hasAssessment) score += weight;
    } else if (field === "career_concerns") {
      if (profile.career_concerns && profile.career_concerns.length > 0) score += weight;
    } else if (profile[field as keyof UserProfile]) {
      score += weight;
    }
  }
  return Math.round(score * 1000) / 10;
}

const BLANK_PROFILE: UserProfile = {
  id: "local",
  user_id: "local",
  age_range: null,
  education_level: null,
  current_field: null,
  years_of_experience: null,
  country: null,
  primary_goal: null,
  career_concerns: null,
  desired_work_environment: null,
  onboarding_completed: false,
  onboarding_step: 0,
  completeness_score: 0,
};

/**
 * Local-device storage adapter.
 *
 * All profile, assessment, and recommendation-cache data is stored
 * exclusively in this browser's IndexedDB — never sent to the backend
 * for persistence. Compute-heavy operations (scoring, embedding search,
 * ranking) still call the backend's stateless endpoints, which perform
 * the computation and return a result without writing anything to the
 * database. See docs/architecture/byos.md.
 */
export class LocalDeviceAdapter implements StorageAdapter {
  readonly providerId = "local_device" as const;

  async getProfile(): Promise<UserProfile | null> {
    return idbGet<UserProfile>(KEYS.profile);
  }

  async saveProfile(updates: ProfileUpdate): Promise<UserProfile> {
    const existing = (await this.getProfile()) ?? BLANK_PROFILE;
    const hasAssessment = (await this.getLatestAssessmentResults()) !== null;

    const merged: UserProfile = {
      ...existing,
      ...updates,
      career_concerns: updates.career_concerns ?? existing.career_concerns,
    };
    merged.completeness_score = computeLocalCompleteness(merged, hasAssessment);

    await idbSet(KEYS.profile, merged);
    return merged;
  }

  async startAssessment(assessmentType = "full"): Promise<StartAssessmentResponse> {
    const { questions, total_questions } = await statelessApi.getQuestions(assessmentType);
    return {
      session: {
        id: `local-${Date.now()}`,
        user_id: "local",
        assessment_type: assessmentType,
        status: "in_progress",
        started_at: new Date().toISOString(),
        completed_at: null,
      },
      questions: questions.map(mapRawQuestion),
      total_questions,
    };
  }

  async submitAssessment(
    _sessionId: string,
    responses: Record<string, number>,
  ): Promise<{ session: unknown; results: LocalAssessmentResults }> {
    const scored = await statelessApi.scoreAssessment(responses);
    const completedAt = new Date().toISOString();

    const results: LocalAssessmentResults = {
      session_id: `local-${Date.now()}`,
      assessment_type: "full",
      completed_at: completedAt,
      dimension_scores: scored.dimension_scores,
      model_version: scored.model_version,
    };

    await idbSet(KEYS.assessment, results);

    // Recompute profile completeness now that an assessment exists.
    const profile = await this.getProfile();
    if (profile) {
      profile.completeness_score = computeLocalCompleteness(profile, true);
      await idbSet(KEYS.profile, profile);
    }

    return {
      session: { id: results.session_id, status: "completed" },
      results,
    };
  }

  async getLatestAssessmentResults(): Promise<LocalAssessmentResults | null> {
    return idbGet<LocalAssessmentResults>(KEYS.assessment);
  }

  async getRecommendations(topK = 10): Promise<RecommendationResult> {
    const assessment = await this.getLatestAssessmentResults();
    if (!assessment) {
      throw new Error("No completed assessment found. Complete an assessment first.");
    }

    const profile = (await this.getProfile()) ?? BLANK_PROFILE;
    const dimensionScores = Object.fromEntries(
      assessment.dimension_scores.map((d) => [d.dimension, d.score]),
    );

    const result = await statelessApi.getRecommendations({
      dimension_scores: dimensionScores,
      profile: {
        education_level: profile.education_level ?? undefined,
        current_field: profile.current_field ?? undefined,
        primary_goal: profile.primary_goal ?? undefined,
        desired_work_environment: profile.desired_work_environment ?? undefined,
        years_of_experience: profile.years_of_experience ?? undefined,
        country: profile.country ?? undefined,
        age_range: profile.age_range ?? undefined,
        career_concerns: profile.career_concerns ?? undefined,
      },
      top_k: topK,
    });

    await idbSet(KEYS.recommendations, result);
    return result;
  }

  async exportSnapshot(): Promise<StorageSnapshot> {
    const [profile, assessment] = await Promise.all([
      this.getProfile(),
      this.getLatestAssessmentResults(),
    ]);
    return { profile, assessment };
  }

  async restoreSnapshot(snapshot: StorageSnapshot): Promise<RestoreSnapshotResult> {
    if (snapshot.assessment) {
      await idbSet(KEYS.assessment, snapshot.assessment);
    }
    if (snapshot.profile) {
      const merged: UserProfile = { ...snapshot.profile };
      merged.completeness_score = computeLocalCompleteness(merged, snapshot.assessment !== null);
      await idbSet(KEYS.profile, merged);
    }
    return {
      profileRestored: snapshot.profile !== null,
      assessmentRestored: snapshot.assessment !== null,
    };
  }

  async clearAll(): Promise<void> {
    await idbClearAll();
  }
}
