import { apiClient } from "@/lib/api/client";
import type { AssessmentQuestion, DimensionScore } from "@/features/assessment/types";
import type { RecommendationResult } from "@/features/careers/types";

/** Raw question shape as returned by the backend (QuestionSchema). */
export interface RawBackendQuestion {
  id: string;
  dimension: string;
  prompt: string;
  reverse_scored: boolean;
}

const LIKERT_OPTIONS = [
  { value: 1, label: "Strongly Disagree" },
  { value: 2, label: "Disagree" },
  { value: 3, label: "Neutral" },
  { value: 4, label: "Agree" },
  { value: 5, label: "Strongly Agree" },
];

/**
 * Maps the backend's QuestionSchema field names (prompt, reverse_scored)
 * to the frontend's AssessmentQuestion shape (text, reversed, options).
 * Shared by both PlatformAdapter and LocalDeviceAdapter so the mapping
 * logic lives in exactly one place.
 */
export function mapRawQuestion(q: RawBackendQuestion): AssessmentQuestion {
  return {
    id: q.id,
    text: q.prompt,
    dimension: q.dimension,
    reversed: q.reverse_scored,
    options: LIKERT_OPTIONS,
  };
}

interface StatelessQuestionsResponse {
  questions: RawBackendQuestion[];
  total_questions: number;
}

interface StatelessScoreResponse {
  model_version: string;
  dimension_scores: DimensionScore[];
}

interface StatelessProfileMeta {
  education_level?: string;
  current_field?: string;
  primary_goal?: string;
  desired_work_environment?: string;
  years_of_experience?: number;
  country?: string;
  age_range?: string;
  career_concerns?: string[];
}

interface StatelessRecommendationRequest {
  dimension_scores: Record<string, number>;
  profile: StatelessProfileMeta;
  top_k: number;
}

/**
 * Client for the backend's stateless (no-persistence) endpoints.
 * Used by LocalDeviceAdapter — every call here computes a result from
 * data supplied in the request; nothing personal is persisted server-side.
 */
export const statelessApi = {
  async getQuestions(assessmentType = "full"): Promise<StatelessQuestionsResponse> {
    const response = await apiClient.get<StatelessQuestionsResponse>(
      `/stateless/questions?assessment_type=${assessmentType}`,
    );
    return response.data;
  },

  async scoreAssessment(responses: Record<string, number>): Promise<StatelessScoreResponse> {
    const response = await apiClient.post<StatelessScoreResponse>("/stateless/score", {
      responses,
    });
    return response.data;
  },

  async getRecommendations(payload: StatelessRecommendationRequest): Promise<RecommendationResult> {
    const response = await apiClient.post<RecommendationResult>(
      "/stateless/recommendations",
      payload,
    );
    return response.data;
  },
};
