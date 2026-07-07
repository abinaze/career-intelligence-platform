import { useLatestResults } from "@/features/assessment/hooks/useAssessment";
import {
  useProfile,
  useRecommendations,
} from "@/features/careers/hooks/useCareers";

/**
 * Aggregates profile, assessment results, and top recommendation
 * into a single dashboard-ready object. Any individual query
 * failing degrades gracefully to placeholder values.
 */
export function useDashboard() {
  const profile = useProfile();
  const latestResults = useLatestResults();
  const recommendations = useRecommendations(1);

  const isLoading =
    profile.isLoading ||
    latestResults.isLoading ||
    recommendations.isLoading;

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
    topCareerScore: topRec
      ? Math.round(topRec.composite_score * 100)
      : null,
    warning: recommendations.data?.warning ?? null,
  };
}
