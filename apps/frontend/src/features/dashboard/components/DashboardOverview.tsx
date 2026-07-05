"use client";

import Link from "next/link";
import { ArrowRight, Brain, Briefcase, UserCircle } from "lucide-react";
import { useDashboard } from "../hooks/useDashboard";
import { StatCard } from "./StatCard";

export function DashboardOverview() {
  const {
    isLoading,
    assessmentStatus,
    profileCompleteness,
    careerMatchCount,
    topCareerTitle,
    topCareerScore,
    warning,
  } = useDashboard();

  // ── Stat cards data ────────────────────────────────────────────────────────
  const assessmentValue =
    assessmentStatus === "completed"
      ? "Completed"
      : assessmentStatus === "in_progress"
        ? "In progress"
        : "Not started";

  const assessmentSub =
    assessmentStatus === "completed"
      ? "View your psychometric profile"
      : "Complete to unlock career matches";

  const careerValue =
    careerMatchCount > 0 ? `${careerMatchCount} matches` : "—";

  const careerSub =
    topCareerTitle && topCareerScore !== null
      ? `Top: ${topCareerTitle} (${topCareerScore}%)`
      : assessmentStatus !== "completed"
        ? "Complete assessment to unlock"
        : "No recommendations yet";

  const profileValue = `${Math.round(profileCompleteness)}%`;
  const profileSub =
    profileCompleteness >= 80
      ? "Great — your profile is detailed"
      : profileCompleteness >= 40
        ? "Add more details to improve accuracy"
        : "Complete your profile to get started";

  return (
    <div className="space-y-8">
      {/* Stat cards */}
      <div className="grid gap-4 md:grid-cols-3">
        <StatCard
          label="Assessment"
          value={assessmentValue}
          sub={assessmentSub}
          href="/assessment"
          loading={isLoading}
          accent={assessmentStatus === "completed"}
        />
        <StatCard
          label="Career Matches"
          value={careerValue}
          sub={careerSub}
          href={careerMatchCount > 0 ? "/careers" : undefined}
          loading={isLoading}
          accent={careerMatchCount > 0}
        />
        <StatCard
          label="Profile Strength"
          value={profileValue}
          sub={profileSub}
          loading={isLoading}
        />
      </div>

      {/* CTA section — shown when assessment not done */}
      {!isLoading && assessmentStatus === "not_started" && (
        <div className="flex flex-col items-start gap-4 rounded-xl border bg-card p-6 shadow-sm sm:flex-row sm:items-center sm:justify-between">
          <div className="flex items-center gap-4">
            <div className="flex h-11 w-11 flex-shrink-0 items-center justify-center rounded-full bg-primary/10">
              <Brain className="h-5 w-5 text-primary" />
            </div>
            <div>
              <p className="font-semibold">Start your psychometric assessment</p>
              <p className="text-sm text-muted-foreground">
                Takes ~10 minutes · Powers all career recommendations
              </p>
            </div>
          </div>
          <Link
            href="/assessment"
            className="inline-flex flex-shrink-0 items-center gap-2 rounded-lg bg-primary px-5 py-2 text-sm font-semibold text-primary-foreground transition-colors hover:bg-primary/90"
          >
            Begin
            <ArrowRight className="h-4 w-4" />
          </Link>
        </div>
      )}

      {/* Top career highlight — shown when recommendations exist */}
      {!isLoading && topCareerTitle && topCareerScore !== null && (
        <div className="rounded-xl border bg-card p-6 shadow-sm">
          <div className="mb-4 flex items-center gap-2">
            <Briefcase className="h-4 w-4 text-primary" />
            <h2 className="text-sm font-semibold uppercase tracking-widest text-muted-foreground">
              Top Career Match
            </h2>
          </div>
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xl font-bold">{topCareerTitle}</p>
              <p className="mt-1 text-sm text-muted-foreground">
                {topCareerScore}% compatibility score
              </p>
            </div>
            <Link
              href="/careers"
              className="inline-flex items-center gap-1 text-sm font-medium text-primary transition-colors hover:text-primary/80"
            >
              View all
              <ArrowRight className="h-3.5 w-3.5" />
            </Link>
          </div>
          {/* Score bar */}
          <div className="mt-4 h-2 w-full overflow-hidden rounded-full bg-secondary">
            <div
              className="h-full rounded-full bg-primary transition-all duration-700"
              style={{ width: `${topCareerScore}%` }}
            />
          </div>
        </div>
      )}

      {/* Profile completeness nudge */}
      {!isLoading && profileCompleteness < 60 && (
        <div className="flex items-center gap-4 rounded-xl border bg-card p-5 shadow-sm">
          <div className="flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-full bg-secondary">
            <UserCircle className="h-5 w-5 text-muted-foreground" />
          </div>
          <div className="flex-1">
            <p className="text-sm font-medium">
              Your profile is {Math.round(profileCompleteness)}% complete
            </p>
            <p className="text-xs text-muted-foreground">
              A fuller profile improves recommendation accuracy
            </p>
          </div>
          {/* Mini progress bar */}
          <div className="w-24">
            <div className="h-1.5 w-full overflow-hidden rounded-full bg-secondary">
              <div
                className="h-full rounded-full bg-primary"
                style={{ width: `${profileCompleteness}%` }}
              />
            </div>
          </div>
        </div>
      )}

      {/* Warning: career DB empty */}
      {warning && (
        <p className="rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800 dark:border-amber-900 dark:bg-amber-950/40 dark:text-amber-300">
          {warning}
        </p>
      )}
    </div>
  );
}
