import type { StartAssessmentResponse } from "@/features/assessment/types";
import type { ProfileUpdate, RecommendationResult, UserProfile } from "@/features/careers/types";
import { dropboxOAuthApi } from "../api/dropboxOAuth.api";
import { mapRawQuestion, statelessApi } from "../api/stateless.api";
import type { DropboxFileContents, LocalAssessmentResults, StorageAdapter } from "../types";
import { DropboxApiError, dropboxClient } from "./dropboxClient";
import { getDropboxTokens, setDropboxTokens } from "./dropboxTokens";

// Mirrors ProfileService._compute_completeness on the backend, same as
// the other two cloud adapters' copies. Kept duplicated deliberately —
// see docs/architecture/byos.md.
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

function computeCompleteness(profile: Partial<UserProfile>, hasAssessment: boolean): number {
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
  id: "dropbox",
  user_id: "dropbox",
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

const BLANK_CONTENTS: DropboxFileContents = {
  profile: null,
  assessment: null,
  recommendations: null,
  updated_at: new Date(0).toISOString(),
};

// Refresh proactively this far ahead of actual expiry.
const REFRESH_SKEW_MS = 60_000;

/**
 * Dropbox storage adapter.
 *
 * All profile, assessment, and recommendation-cache data lives in a
 * single JSON file in the user's own Dropbox app folder — never on this
 * platform's servers. Compute still goes through the backend's
 * stateless endpoints, same as the other two cloud adapters; only the
 * storage target differs. See docs/architecture/byos.md.
 *
 * Structured like OneDriveAdapter (path-addressable file, no separate
 * file-ID lookup step) rather than GoogleDriveAdapter's ID-based
 * approach — Dropbox's "App folder" access type means every path is
 * already sandboxed to this app, so there's nothing to search for.
 *
 * Token handling is the same shape as the other two adapters: proactive
 * refresh near expiry, one reactive retry on a 401 from Dropbox itself.
 * Unlike OneDriveAdapter, disconnect *can* revoke the token server-side
 * (Dropbox has a real revoke endpoint) — but that call lives in
 * DropboxConnect.tsx, not here, same as the other adapters keep
 * connect/disconnect orchestration out of the adapter itself.
 */
export class DropboxAdapter implements StorageAdapter {
  readonly providerId = "dropbox" as const;

  private async getValidAccessToken(): Promise<string> {
    const tokens = await getDropboxTokens();
    if (!tokens) {
      throw new Error("Dropbox is not connected. Please reconnect in Settings → Storage.");
    }

    const expiresAt = new Date(tokens.expires_at).getTime();
    if (expiresAt - Date.now() > REFRESH_SKEW_MS) {
      return tokens.access_token;
    }

    if (!tokens.refresh_token) {
      throw new Error(
        "Your Dropbox session has expired and can't be refreshed automatically. " +
          "Please reconnect in Settings → Storage.",
      );
    }

    const refreshed = await dropboxOAuthApi.refresh(tokens.refresh_token);
    await setDropboxTokens(refreshed);
    return refreshed.access_token;
  }

  /**
   * Runs a Dropbox API call with a valid token, retrying exactly once
   * via a forced refresh if Dropbox itself returns 401 (covers access
   * revoked externally, which a proactive expiry check can't catch).
   */
  private async callWithRetry<T>(fn: (accessToken: string) => Promise<T>): Promise<T> {
    const token = await this.getValidAccessToken();
    try {
      return await fn(token);
    } catch (error) {
      if (error instanceof DropboxApiError && error.status === 401) {
        const tokens = await getDropboxTokens();
        if (!tokens?.refresh_token) throw error;
        const refreshed = await dropboxOAuthApi.refresh(tokens.refresh_token);
        await setDropboxTokens(refreshed);
        return fn(refreshed.access_token);
      }
      throw error;
    }
  }

  private async readFile(): Promise<DropboxFileContents> {
    return this.callWithRetry(async (token) => {
      const exists = await dropboxClient.fileExists(token);
      if (!exists) return BLANK_CONTENTS;
      return dropboxClient.readDataFile(token);
    });
  }

  private async writeFile(
    patch: Partial<DropboxFileContents>,
    knownCurrent?: DropboxFileContents,
  ): Promise<DropboxFileContents> {
    return this.callWithRetry(async (token) => {
      let current = knownCurrent;
      if (!current) {
        const exists = await dropboxClient.fileExists(token);
        current = exists ? await dropboxClient.readDataFile(token) : BLANK_CONTENTS;
      }
      const merged: DropboxFileContents = {
        ...current,
        ...patch,
        updated_at: new Date().toISOString(),
      };
      await dropboxClient.writeDataFile(token, merged);
      return merged;
    });
  }

  async getProfile(): Promise<UserProfile | null> {
    const file = await this.readFile();
    return file.profile;
  }

  async saveProfile(updates: ProfileUpdate): Promise<UserProfile> {
    const current = await this.readFile();
    const existing = current.profile ?? BLANK_PROFILE;

    const merged: UserProfile = {
      ...existing,
      ...updates,
      career_concerns: updates.career_concerns ?? existing.career_concerns,
    };
    merged.completeness_score = computeCompleteness(merged, current.assessment !== null);

    await this.writeFile({ profile: merged }, current);
    return merged;
  }

  async startAssessment(assessmentType = "full"): Promise<StartAssessmentResponse> {
    const { questions, total_questions } = await statelessApi.getQuestions(assessmentType);
    return {
      session: {
        id: `dropbox-${Date.now()}`,
        user_id: "dropbox",
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
    const results: LocalAssessmentResults = {
      session_id: `dropbox-${Date.now()}`,
      assessment_type: "full",
      completed_at: new Date().toISOString(),
      dimension_scores: scored.dimension_scores,
      model_version: scored.model_version,
    };

    const current = await this.readFile();
    const updatedProfile = current.profile
      ? { ...current.profile, completeness_score: computeCompleteness(current.profile, true) }
      : current.profile;

    await this.writeFile({ assessment: results, profile: updatedProfile }, current);

    return {
      session: { id: results.session_id, status: "completed" },
      results,
    };
  }

  async getLatestAssessmentResults(): Promise<LocalAssessmentResults | null> {
    const file = await this.readFile();
    return file.assessment;
  }

  async getRecommendations(topK = 10): Promise<RecommendationResult> {
    const current = await this.readFile();
    const assessment = current.assessment;
    if (!assessment) {
      throw new Error("No completed assessment found. Complete an assessment first.");
    }

    const profile = current.profile ?? BLANK_PROFILE;
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

    await this.writeFile({ recommendations: result }, current);
    return result;
  }

  async clearAll(): Promise<void> {
    await this.callWithRetry(async (token) => {
      const exists = await dropboxClient.fileExists(token);
      if (exists) {
        await dropboxClient.deleteDataFile(token);
      }
    });
  }
}
