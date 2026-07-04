/**
 * Assessment feature types.
 * Mirror the backend Pydantic schemas exactly.
 */

// ── Question ──────────────────────────────────────────────────────────────────

export interface AssessmentQuestion {
  id: string;
  text: string;
  dimension: string;
  reversed: boolean;
  options: QuestionOption[];
}

export interface QuestionOption {
  value: number; // 1–5
  label: string;
}

// ── Session ───────────────────────────────────────────────────────────────────

export type AssessmentStatus = "not_started" | "in_progress" | "completed";

export interface AssessmentSession {
  id: string;
  user_id: string;
  assessment_type: string;
  status: AssessmentStatus;
  started_at: string;
  completed_at: string | null;
}

// ── Results ───────────────────────────────────────────────────────────────────

export interface DimensionScore {
  dimension: string;
  display_name: string;
  score: number; // 0-100
  confidence: number; // 0-1
  percentile: number | null;
}

export interface AssessmentResults {
  session_id: string;
  assessment_type: string;
  completed_at: string;
  dimension_scores: DimensionScore[];
  model_version: string;
}

// ── API request / response shapes ─────────────────────────────────────────────

export interface StartAssessmentResponse {
  session: AssessmentSession;
  questions: AssessmentQuestion[];
  total_questions: number;
}

export interface SubmitAssessmentRequest {
  session_id: string;
  responses: Record<string, number>; // question_id → value (1–5)
}

export interface SubmitAssessmentResponse {
  session: AssessmentSession;
  results: AssessmentResults;
}

// ── UI State ──────────────────────────────────────────────────────────────────

export type AssessmentStep = "intro" | "questions" | "results";

export interface AssessmentStoreState {
  step: AssessmentStep;
  sessionId: string | null;
  questions: AssessmentQuestion[];
  currentIndex: number;
  responses: Record<string, number>;
  results: AssessmentResults | null;
  isLoading: boolean;
  error: string | null;
}
