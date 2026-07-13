import { apiClient } from "@/lib/api/client";
import { getActiveStorageAdapter } from "@/features/storage/adapters/registry";
import type {
  StartAssessmentResponse,
  SubmitAssessmentRequest,
  SubmitAssessmentResponse,
  AssessmentResults,
} from "../types";

/**
 * Assessment API layer.
 *
 * start(), submit(), and getLatestResults() delegate to the active
 * storage adapter (see features/storage) so behavior automatically
 * follows the user's chosen storage provider. Default provider is
 * "platform", so existing behavior is unchanged unless the user opts
 * into local-device storage in Settings.
 *
 * getResults(sessionId) remains platform-only: local-device storage
 * has no concept of multiple historical sessions by ID, only "the
 * latest" result.
 */
export const assessmentApi = {
  /**
   * Start a new psychometric assessment session.
   * Returns the session metadata and the full question list.
   */
  async start(): Promise<StartAssessmentResponse> {
    const adapter = getActiveStorageAdapter();
    return adapter.startAssessment("full");
  },

  /**
   * Submit all responses and retrieve scored results.
   */
  async submit(payload: SubmitAssessmentRequest): Promise<SubmitAssessmentResponse> {
    const adapter = getActiveStorageAdapter();
    const { session, results } = await adapter.submitAssessment(
      payload.session_id,
      payload.responses,
    );
    return {
      session: session as SubmitAssessmentResponse["session"],
      results,
    };
  },

  /**
   * Retrieve results for a completed session by ID. Platform storage only.
   */
  async getResults(sessionId: string): Promise<AssessmentResults> {
    const response = await apiClient.get<AssessmentResults>(`/assessment/${sessionId}/results`);
    return response.data;
  },

  /**
   * Retrieve the most recent completed assessment results for the
   * authenticated user, or null if none exists.
   */
  async getLatestResults(): Promise<AssessmentResults | null> {
    const adapter = getActiveStorageAdapter();
    try {
      return await adapter.getLatestAssessmentResults();
    } catch {
      return null;
    }
  },
};
