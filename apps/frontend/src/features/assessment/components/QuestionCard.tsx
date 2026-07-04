"use client";

import { cn } from "@/lib/utils";
import type { AssessmentQuestion } from "../types";

const LIKERT_OPTIONS = [
  { value: 1, label: "Strongly Disagree" },
  { value: 2, label: "Disagree" },
  { value: 3, label: "Neutral" },
  { value: 4, label: "Agree" },
  { value: 5, label: "Strongly Agree" },
] as const;

interface QuestionCardProps {
  question: AssessmentQuestion;
  questionNumber: number;
  totalQuestions: number;
  selectedValue: number | undefined;
  onAnswer: (questionId: string, value: number) => void;
}

export function QuestionCard({
  question,
  questionNumber,
  totalQuestions,
  selectedValue,
  onAnswer,
}: QuestionCardProps) {
  return (
    <div className="rounded-xl border bg-card p-8 shadow-sm">
      {/* Question number */}
      <p className="text-xs font-medium uppercase tracking-widest text-muted-foreground">
        Question {questionNumber} of {totalQuestions}
      </p>

      {/* Question text */}
      <p className="mt-4 text-xl font-semibold leading-relaxed text-foreground">
        {question.text}
      </p>

      {/* Likert scale */}
      <div className="mt-8">
        {/* Labels */}
        <div className="mb-3 flex justify-between text-xs text-muted-foreground">
          <span>Strongly Disagree</span>
          <span>Strongly Agree</span>
        </div>

        {/* Options */}
        <div className="flex items-center justify-between gap-2">
          {LIKERT_OPTIONS.map(({ value, label }) => {
            const isSelected = selectedValue === value;
            return (
              <button
                key={value}
                type="button"
                aria-label={label}
                aria-pressed={isSelected}
                onClick={() => onAnswer(question.id, value)}
                className={cn(
                  "flex h-12 w-12 flex-shrink-0 items-center justify-center rounded-full",
                  "text-sm font-semibold transition-all duration-150",
                  "border-2 focus-visible:ring-2 focus-visible:ring-ring",
                  isSelected
                    ? "border-primary bg-primary text-primary-foreground scale-110 shadow-md"
                    : "border-border bg-background text-muted-foreground hover:border-primary/50 hover:bg-primary/5",
                )}
              >
                {value}
              </button>
            );
          })}
        </div>
      </div>
    </div>
  );
}
