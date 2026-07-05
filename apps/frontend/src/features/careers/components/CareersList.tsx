"use client";

import Link from "next/link";
import { Briefcase, AlertCircle, Loader2 } from "lucide-react";
import { useRecommendations } from "../hooks/useCareers";
import { CareerCard } from "./CareerCard";

export function CareersList() {
  const { data, isLoading, error } = useRecommendations(10);

  // ── Loading ───────────────────────────────────────────────────────────────
  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center rounded-xl border bg-card py-20 text-center shadow-sm">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
        <p className="mt-4 text-sm text-muted-foreground">
          Generating your recommendations…
        </p>
      </div>
    );
  }

  // ── Error: no assessment yet ──────────────────────────────────────────────
  if (error) {
    return (
      <div className="flex flex-col items-center justify-center rounded-xl border bg-card py-20 text-center shadow-sm">
        <div className="flex h-12 w-12 items-center justify-center rounded-full bg-amber-100 dark:bg-amber-950">
          <AlertCircle className="h-6 w-6 text-amber-600 dark:text-amber-400" />
        </div>
        <h3 className="mt-4 text-base font-semibold">Assessment required</h3>
        <p className="mt-2 max-w-xs text-sm text-muted-foreground">
          Complete your psychometric assessment to unlock personalised career
          recommendations.
        </p>
        <Link
          href="/assessment"
          className="mt-6 inline-flex items-center gap-2 rounded-lg bg-primary px-5 py-2 text-sm font-semibold text-primary-foreground transition-colors hover:bg-primary/90"
        >
          Start Assessment
        </Link>
      </div>
    );
  }

  // ── Warning: career DB empty ──────────────────────────────────────────────
  if (data?.warning) {
    return (
      <div className="flex flex-col items-center justify-center rounded-xl border bg-card py-20 text-center shadow-sm">
        <Briefcase className="h-10 w-10 text-muted-foreground/40" />
        <h3 className="mt-4 text-base font-semibold">No careers loaded</h3>
        <p className="mt-2 max-w-xs text-sm text-muted-foreground">
          {data.warning}
        </p>
      </div>
    );
  }

  // ── Empty ─────────────────────────────────────────────────────────────────
  if (!data?.recommendations.length) {
    return (
      <div className="flex flex-col items-center justify-center rounded-xl border bg-card py-20 text-center shadow-sm">
        <Briefcase className="h-10 w-10 text-muted-foreground/40" />
        <h3 className="mt-4 text-base font-semibold">No recommendations yet</h3>
        <p className="mt-2 text-sm text-muted-foreground">
          Check back after your assessment results are processed.
        </p>
      </div>
    );
  }

  // ── Results ───────────────────────────────────────────────────────────────
  return (
    <div className="space-y-4">
      {/* Profile completeness banner */}
      {data.profile_completeness < 60 && (
        <div className="flex items-start gap-3 rounded-xl border border-amber-200 bg-amber-50 p-4 dark:border-amber-900 dark:bg-amber-950/40">
          <AlertCircle className="mt-0.5 h-4 w-4 flex-shrink-0 text-amber-600 dark:text-amber-400" />
          <p className="text-sm text-amber-800 dark:text-amber-300">
            Your profile is{" "}
            <strong>{Math.round(data.profile_completeness)}% complete</strong>.
            Add more details to improve recommendation accuracy.
          </p>
        </div>
      )}

      {/* Career cards */}
      {data.recommendations.map((rec, i) => (
        <CareerCard key={rec.career_id} recommendation={rec} rank={i + 1} />
      ))}
    </div>
  );
}
