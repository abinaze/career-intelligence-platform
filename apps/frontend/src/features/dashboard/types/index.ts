/**
 * Dashboard feature types.
 */

export interface DashboardStat {
  label: string;
  value: string;
  sub: string;
  href?: string;
}

export interface DashboardData {
  assessmentStatus: "not_started" | "in_progress" | "completed";
  topCareerTitle: string | null;
  topCareerScore: number | null;
  profileCompleteness: number;
  careerMatchCount: number;
}
