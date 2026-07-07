/**
 * Careers feature types.
 * Mirror the backend recommendation response schemas exactly.
 */

export interface FactorExplanation {
  factor: string;
  label: string;
  score: number;
  driver: "strong match" | "moderate match" | "partial match" | "weak match";
  detail: string;
}

export interface CareerExplanation {
  career_id: string;
  onet_code: string;
  title: string;
  summary: string;
  confidence_band: "high" | "medium" | "low";
  factors: FactorExplanation[];
  top_matching_traits: string[];
}

export interface CareerRecommendation {
  career_id: string;
  onet_code: string;
  title: string;
  broad_category: string;
  description: string;
  median_salary_usd: number | null;
  outlook_percentile: number | null;
  composite_score: number;
  similarity_score: number;
  riasec_score: number;
  explanation: CareerExplanation;
}

export interface RecommendationResult {
  user_id: string;
  profile_completeness: number;
  recommendations: CareerRecommendation[];
  warning: string | null;
}

export interface UserProfile {
  id: string;
  user_id: string;
  age_range: string | null;
  education_level: string | null;
  current_field: string | null;
  years_of_experience: number | null;
  country: string | null;
  primary_goal: string | null;
  career_concerns: string[] | null;
  desired_work_environment: string | null;
  onboarding_completed: boolean;
  onboarding_step: number;
  completeness_score: number;
}

export interface ProfileUpdate {
  age_range?: string;
  education_level?: string;
  current_field?: string;
  years_of_experience?: number;
  country?: string;
  primary_goal?: string;
  career_concerns?: string[];
  desired_work_environment?: string;
  onboarding_step?: number;
  onboarding_completed?: boolean;
}

export type ConfidenceBand = "high" | "medium" | "low";

export const CONFIDENCE_STYLES: Record<
  ConfidenceBand,
  { badge: string; label: string }
> = {
  high: {
    badge:
      "text-emerald-700 bg-emerald-50 dark:text-emerald-400 dark:bg-emerald-950",
    label: "High confidence",
  },
  medium: {
    badge:
      "text-amber-700 bg-amber-50 dark:text-amber-400 dark:bg-amber-950",
    label: "Medium confidence",
  },
  low: {
    badge: "text-rose-700 bg-rose-50 dark:text-rose-400 dark:bg-rose-950",
    label: "Low confidence",
  },
};
