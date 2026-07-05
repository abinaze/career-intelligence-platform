/**
 * Careers feature types.
 * Mirror the backend recommendation response schemas exactly.
 */

// ── Factor explanation ────────────────────────────────────────────────────────

export interface FactorExplanation {
  factor: string;
  label: string;
  score: number;
  driver: string; // "strong match" | "moderate match" | "partial match" | "weak match"
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

// ── Career recommendation ─────────────────────────────────────────────────────

export interface CareerRecommendation {
  career_id: string;
  onet_code: string;
  title: string;
  broad_category: string;
  description: string;
  median_salary_usd: number | null;
  outlook_percentile: number | null;
  composite_score: number; // 0-1
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

// ── Profile ───────────────────────────────────────────────────────────────────

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
  completeness_score: number; // 0-100
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

// ── UI state ──────────────────────────────────────────────────────────────────

export type ConfidenceBand = "high" | "medium" | "low";

export const CONFIDENCE_COLOURS: Record<ConfidenceBand, string> = {
  high: "text-emerald-600 bg-emerald-50 dark:text-emerald-400 dark:bg-emerald-950",
  medium: "text-amber-600 bg-amber-50 dark:text-amber-400 dark:bg-amber-950",
  low: "text-rose-600 bg-rose-50 dark:text-rose-400 dark:bg-rose-950",
};
