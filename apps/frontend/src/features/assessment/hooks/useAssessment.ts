import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { assessmentApi } from "../api/assessment.api";
import { useAssessmentStore } from "../store/assessment.store";

export const ASSESSMENT_KEYS = {
  all: ["assessment"] as const,
  latest: () => [...ASSESSMENT_KEYS.all, "latest"] as const,
  results: (id: string) => [...ASSESSMENT_KEYS.all, "results", id] as const,
};

/**
 * Fetch the most recently completed assessment results.
 * Returns null when no assessment has been completed yet.
 */
export function useLatestResults() {
  return useQuery({
    queryKey: ASSESSMENT_KEYS.latest(),
    queryFn: () => assessmentApi.getLatestResults(),
    staleTime: 5 * 60 * 1000,
    retry: false,
  });
}

/**
 * Fetch results for a specific session.
 */
export function useAssessmentResults(sessionId: string | null) {
  return useQuery({
    queryKey: ASSESSMENT_KEYS.results(sessionId ?? ""),
    queryFn: () => assessmentApi.getResults(sessionId!),
    enabled: !!sessionId,
    staleTime: Infinity,
  });
}

/**
 * Mutation: start a new assessment session.
 * On success, the store is updated and the query cache is invalidated
 * so the dashboard re-fetches status automatically.
 */
export function useStartAssessment() {
  const queryClient = useQueryClient();
  const store = useAssessmentStore();

  return useMutation({
    mutationFn: () => store.startAssessment(),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ASSESSMENT_KEYS.all });
    },
  });
}

/**
 * Mutation: submit all responses.
 * Invalidates latest results so the dashboard shows the new score.
 */
export function useSubmitAssessment() {
  const queryClient = useQueryClient();
  const store = useAssessmentStore();

  return useMutation({
    mutationFn: () => store.submitAssessment(),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ASSESSMENT_KEYS.all });
    },
  });
}

/**
 * Convenience hook that gives components everything they need
 * for the assessment flow in one import.
 */
export function useAssessment() {
  const store = useAssessmentStore();
  const start = useStartAssessment();
  const submit = useSubmitAssessment();

  return {
    // State
    step: store.step,
    sessionId: store.sessionId,
    questions: store.questions,
    currentIndex: store.currentIndex,
    currentQuestion: store.questions[store.currentIndex] ?? null,
    responses: store.responses,
    results: store.results,
    isLoading: store.isLoading || start.isPending || submit.isPending,
    error: store.error,

    // Derived
    progress: store.progress(),
    canGoNext: store.canGoNext(),
    canSubmit: store.canSubmit(),
    totalQuestions: store.questions.length,

    // Actions
    startAssessment: start.mutate,
    answerQuestion: store.answerQuestion,
    goToNext: store.goToNext,
    goToPrev: store.goToPrev,
    submitAssessment: submit.mutate,
    resetAssessment: store.resetAssessment,
    clearError: store.clearError,
  };
}
