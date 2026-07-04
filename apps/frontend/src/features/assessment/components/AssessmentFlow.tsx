"use client";

import { Brain, ChevronLeft, ChevronRight, RotateCcw } from "lucide-react";
import { useAssessment } from "../hooks/useAssessment";
import { QuestionCard } from "./QuestionCard";
import { ProgressBar } from "./ProgressBar";
import { ResultsChart } from "./ResultsChart";

export function AssessmentFlow() {
  const {
    step,
    currentQuestion,
    currentIndex,
    totalQuestions,
    responses,
    results,
    progress,
    canGoNext,
    canSubmit,
    isLoading,
    error,
    startAssessment,
    answerQuestion,
    goToNext,
    goToPrev,
    submitAssessment,
    resetAssessment,
  } = useAssessment();

  // ── Intro ───────────────────────────────────────────────────────────────────
  if (step === "intro") {
    return (
      <div className="rounded-xl border bg-card p-10 text-center shadow-sm">
        <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-full bg-primary/10">
          <Brain className="h-7 w-7 text-primary" />
        </div>
        <h2 className="mt-5 text-2xl font-bold">Psychometric Assessment</h2>
        <p className="mt-3 mx-auto max-w-md text-muted-foreground">
          This 10-minute assessment measures your Big Five personality traits
          and RIASEC vocational interests across 11 dimensions to power your
          personalised career recommendations.
        </p>
        <ul className="mt-6 mx-auto max-w-xs space-y-2 text-sm text-left text-muted-foreground">
          {[
            "~40 questions, rated 1–5",
            "No right or wrong answers",
            "Results are instant",
            "Powers your career matches",
          ].map((item) => (
            <li key={item} className="flex items-center gap-2">
              <span className="h-1.5 w-1.5 rounded-full bg-primary flex-shrink-0" />
              {item}
            </li>
          ))}
        </ul>

        {error && (
          <p className="mt-4 text-sm text-destructive">{error}</p>
        )}

        <button
          onClick={() => startAssessment()}
          disabled={isLoading}
          className="mt-8 inline-flex items-center gap-2 rounded-lg bg-primary px-8 py-2.5 text-sm font-semibold text-primary-foreground transition-colors hover:bg-primary/90 disabled:opacity-60 disabled:cursor-not-allowed"
        >
          {isLoading ? "Starting…" : "Begin Assessment"}
        </button>
      </div>
    );
  }

  // ── Questions ───────────────────────────────────────────────────────────────
  if (step === "questions" && currentQuestion) {
    const isLast = currentIndex === totalQuestions - 1;

    return (
      <div className="space-y-6">
        <ProgressBar value={progress} />

        <QuestionCard
          question={currentQuestion}
          questionNumber={currentIndex + 1}
          totalQuestions={totalQuestions}
          selectedValue={responses[currentQuestion.id]}
          onAnswer={answerQuestion}
        />

        {error && (
          <p className="text-sm text-destructive">{error}</p>
        )}

        <div className="flex items-center justify-between">
          <button
            onClick={goToPrev}
            disabled={currentIndex === 0}
            className="inline-flex items-center gap-1 rounded-lg border px-4 py-2 text-sm font-medium transition-colors hover:bg-accent disabled:opacity-40 disabled:cursor-not-allowed"
          >
            <ChevronLeft className="h-4 w-4" />
            Previous
          </button>

          {isLast ? (
            <button
              onClick={() => submitAssessment()}
              disabled={!canSubmit || isLoading}
              className="inline-flex items-center gap-2 rounded-lg bg-primary px-6 py-2 text-sm font-semibold text-primary-foreground transition-colors hover:bg-primary/90 disabled:opacity-60 disabled:cursor-not-allowed"
            >
              {isLoading ? "Submitting…" : "Submit Assessment"}
            </button>
          ) : (
            <button
              onClick={goToNext}
              disabled={!canGoNext}
              className="inline-flex items-center gap-1 rounded-lg bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground transition-colors hover:bg-primary/90 disabled:opacity-60 disabled:cursor-not-allowed"
            >
              Next
              <ChevronRight className="h-4 w-4" />
            </button>
          )}
        </div>
      </div>
    );
  }

  // ── Results ─────────────────────────────────────────────────────────────────
  if (step === "results" && results) {
    const sorted = [...results.dimension_scores].sort(
      (a, b) => b.score - a.score,
    );
    const top3 = sorted.slice(0, 3);

    return (
      <div className="space-y-6">
        {/* Header */}
        <div className="rounded-xl border bg-card p-6 shadow-sm">
          <h2 className="text-xl font-bold">Your Psychometric Profile</h2>
          <p className="mt-1 text-sm text-muted-foreground">
            Assessment completed ·{" "}
            {new Date(results.completed_at).toLocaleDateString()}
          </p>
        </div>

        {/* Chart */}
        <div className="rounded-xl border bg-card p-6 shadow-sm">
          <h3 className="mb-4 text-sm font-semibold uppercase tracking-widest text-muted-foreground">
            Dimension Overview
          </h3>
          <ResultsChart scores={results.dimension_scores} />
        </div>

        {/* Top strengths */}
        <div className="rounded-xl border bg-card p-6 shadow-sm">
          <h3 className="mb-4 text-sm font-semibold uppercase tracking-widest text-muted-foreground">
            Top Strengths
          </h3>
          <div className="space-y-4">
            {top3.map((s) => (
              <div key={s.dimension}>
                <div className="mb-1 flex items-center justify-between text-sm">
                  <span className="font-medium">{s.display_name}</span>
                  <span className="text-muted-foreground">
                    {Math.round(s.score)}/100
                  </span>
                </div>
                <div className="h-2 w-full overflow-hidden rounded-full bg-secondary">
                  <div
                    className="h-full rounded-full bg-primary transition-all duration-500"
                    style={{ width: `${s.score}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* All scores grid */}
        <div className="rounded-xl border bg-card p-6 shadow-sm">
          <h3 className="mb-4 text-sm font-semibold uppercase tracking-widest text-muted-foreground">
            All Dimensions
          </h3>
          <div className="grid gap-3 sm:grid-cols-2">
            {results.dimension_scores.map((s) => (
              <div
                key={s.dimension}
                className="flex items-center justify-between rounded-lg bg-secondary/50 px-4 py-3"
              >
                <span className="text-sm font-medium">{s.display_name}</span>
                <span className="text-sm font-bold text-primary">
                  {Math.round(s.score)}
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* Retake */}
        <div className="flex justify-center">
          <button
            onClick={resetAssessment}
            className="inline-flex items-center gap-2 text-sm text-muted-foreground transition-colors hover:text-foreground"
          >
            <RotateCcw className="h-3.5 w-3.5" />
            Retake Assessment
          </button>
        </div>
      </div>
    );
  }

  return null;
}
