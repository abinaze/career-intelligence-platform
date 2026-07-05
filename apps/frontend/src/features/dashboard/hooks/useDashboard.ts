import { useProfile, useRecommendations } from "@/features/careers/hooks/useCareers";
import { useLatestResults } from "@/features/assessment/hooks/useAssessment";

/**
 * Aggregates data from three backend sources into one dashboard-ready shape.
 * Any individual query failing is handled gracefully — the dashboard
 * degrades to placeholder values rather than throwing.
 */
export function useDashboard() {
  const profile = useProfile();
  const latestResults = useLatestResults();
  const recommendations = useRecommendations(1); // only need the top match

  const isLoading =
    profile.isLoading || latestResults.isLoading || recommendations.isLoading;

  const assessmentStatus = latestResults.data
    ? "completed"
    : latestResults.isLoading
      ? "in_progress"
      : "not_started";

  const topRec = recommendations.data?.recommendations[0] ?? null;

  return {
    isLoading,
    assessmentStatus,
    profileCompleteness: profile.data?.completeness_score ?? 0,
    careerMatchCount: recommendations.data?.recommendations.length ?? 0,
    topCareerTitle: topRec?.title ?? null,
    topCareerScore: topRec ? Math.round(topRec.composite_score * 100) : null,
    warning: recommendations.data?.warning ?? null,
  };
}
