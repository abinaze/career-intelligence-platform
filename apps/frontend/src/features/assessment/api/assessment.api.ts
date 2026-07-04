import { apiClient } from "@/lib/api/client";
import type {
  StartAssessmentResponse,
  SubmitAssessmentRequest,
  SubmitAssessmentResponse,
  AssessmentResults,
} from "../types";

/**
 * Assessment API layer.
 * All HTTP calls for the assessment feature live here.
 */
export const assessmentApi = {
  /**
   * Start a new psychometric assessment session.
   * Returns the session metadata and the full question list.
   */
  async start(): Promise<StartAssessmentResponse> {
    const response = await apiClient.post<StartAssessmentResponse>(
      "/assessment/start",
    );
    return response.data;
  },

  /**
   * Submit all responses and retrieve scored results.
   */
  async submit(
    payload: SubmitAssessmentRequest,
  ): Promise<SubmitAssessmentResponse> {
    const response = await apiClient.post<SubmitAssessmentResponse>(
      "/assessment/submit",
      payload,
    );
    return response.data;
  },

  /**
   * Retrieve results for a completed session by ID.
   */
  async getResults(sessionId: string): Promise<AssessmentResults> {
    const response = await apiClient.get<AssessmentResults>(
      `/assessment/${sessionId}/results`,
    );
    return response.data;
  },

  /**
   * Retrieve the most recent completed assessment results for the
   * authenticated user, or null if none exists.
   */
  async getLatestResults(): Promise<AssessmentResults | null> {
    try {
      const response =
        await apiClient.get<AssessmentResults>("/assessment/latest");
      return response.data;
    } catch {
      return null;
    }
  },
};
