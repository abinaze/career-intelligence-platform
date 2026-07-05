"use client";

import { useState } from "react";
import { ChevronDown, ChevronUp, DollarSign, TrendingUp } from "lucide-react";
import { cn } from "@/lib/utils";
import { CONFIDENCE_COLOURS } from "../types";
import type { CareerRecommendation } from "../types";

interface CareerCardProps {
  recommendation: CareerRecommendation;
  rank: number;
}

export function CareerCard({ recommendation: r, rank }: CareerCardProps) {
  const [expanded, setExpanded] = useState(false);
  const pct = Math.round(r.composite_score * 100);

  return (
    <div className="rounded-xl border bg-card shadow-sm transition-shadow hover:shadow-md">
      {/* Header */}
      <div className="flex items-start gap-4 p-5">
        {/* Rank badge */}
        <div className="flex h-9 w-9 flex-shrink-0 items-center justify-center rounded-full bg-primary/10 text-sm font-bold text-primary">
          {rank}
        </div>

        {/* Title block */}
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-2">
            <h3 className="text-base font-semibold leading-tight">{r.title}</h3>
            <span
              className={cn(
                "inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium capitalize",
                CONFIDENCE_COLOURS[r.explanation.confidence_band],
              )}
            >
              {r.explanation.confidence_band} confidence
            </span>
          </div>
          <p className="mt-0.5 text-xs text-muted-foreground">
            {r.broad_category}
          </p>

          {/* Quick stats */}
          <div className="mt-3 flex flex-wrap items-center gap-4 text-xs text-muted-foreground">
            {r.median_salary_usd && (
              <span className="flex items-center gap-1">
                <DollarSign className="h-3 w-3" />
                {new Intl.NumberFormat("en-US", {
                  style: "currency",
                  currency: "USD",
                  maximumFractionDigits: 0,
                }).format(r.median_salary_usd)}
                /yr
              </span>
            )}
            {r.outlook_percentile && (
              <span className="flex items-center gap-1">
                <TrendingUp className="h-3 w-3" />
                {Math.round(r.outlook_percentile)}th percentile outlook
              </span>
            )}
          </div>
        </div>

        {/* Match score */}
        <div className="flex flex-shrink-0 flex-col items-end gap-1">
          <span className="text-2xl font-bold text-primary">{pct}%</span>
          <span className="text-xs text-muted-foreground">match</span>
        </div>
      </div>

      {/* Score bar */}
      <div className="px-5 pb-4">
        <div className="h-1.5 w-full overflow-hidden rounded-full bg-secondary">
          <div
            className="h-full rounded-full bg-primary transition-all duration-500"
            style={{ width: `${pct}%` }}
          />
        </div>
      </div>

      {/* Summary */}
      <div className="border-t px-5 py-3">
        <p className="text-sm text-muted-foreground">
          {r.explanation.summary}
        </p>
      </div>

      {/* Expand / collapse explanation */}
      <div className="border-t">
        <button
          onClick={() => setExpanded((v) => !v)}
          className="flex w-full items-center justify-between px-5 py-3 text-xs font-medium text-muted-foreground transition-colors hover:bg-accent/50"
        >
          <span>Why this career?</span>
          {expanded ? (
            <ChevronUp className="h-3.5 w-3.5" />
          ) : (
            <ChevronDown className="h-3.5 w-3.5" />
          )}
        </button>

        {expanded && (
          <div className="space-y-3 px-5 pb-5">
            {/* Top traits */}
            {r.explanation.top_matching_traits.length > 0 && (
              <div className="flex flex-wrap gap-1.5">
                {r.explanation.top_matching_traits.map((trait) => (
                  <span
                    key={trait}
                    className="rounded-full bg-primary/10 px-2.5 py-0.5 text-xs font-medium text-primary"
                  >
                    {trait}
                  </span>
                ))}
              </div>
            )}

            {/* Factor breakdown */}
            <div className="space-y-2">
              {r.explanation.factors.map((factor) => (
                <div key={factor.factor}>
                  <div className="mb-1 flex items-center justify-between text-xs">
                    <span className="font-medium">{factor.label}</span>
                    <span className="text-muted-foreground capitalize">
                      {factor.driver}
                    </span>
                  </div>
                  <div className="h-1 w-full overflow-hidden rounded-full bg-secondary">
                    <div
                      className="h-full rounded-full bg-primary/60"
                      style={{ width: `${Math.round(factor.score * 100)}%` }}
                    />
                  </div>
                  <p className="mt-1 text-xs text-muted-foreground">
                    {factor.detail}
                  </p>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
