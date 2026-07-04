import { create } from "zustand";
import { immer } from "zustand/middleware/immer";
import { assessmentApi } from "../api/assessment.api";
import type {
  AssessmentQuestion,
  AssessmentResults,
  AssessmentStep,
} from "../types";

interface AssessmentStore {
  // State
  step: AssessmentStep;
  sessionId: string | null;
  questions: AssessmentQuestion[];
  currentIndex: number;
  responses: Record<string, number>;
  results: AssessmentResults | null;
  isLoading: boolean;
  error: string | null;

  // Actions
  startAssessment: () => Promise<void>;
  answerQuestion: (questionId: string, value: number) => void;
  goToNext: () => void;
  goToPrev: () => void;
  submitAssessment: () => Promise<void>;
  resetAssessment: () => void;
  clearError: () => void;

  // Derived helpers (not stored — computed on access)
  progress: () => number;
  canGoNext: () => boolean;
  canSubmit: () => boolean;
}

const INITIAL_STATE = {
  step: "intro" as AssessmentStep,
  sessionId: null,
  questions: [],
  currentIndex: 0,
  responses: {},
  results: null,
  isLoading: false,
  error: null,
};

export const useAssessmentStore = create<AssessmentStore>()(
  immer((set, get) => ({
    ...INITIAL_STATE,

    startAssessment: async () => {
      set((s) => {
        s.isLoading = true;
        s.error = null;
      });
      try {
        const { session, questions } = await assessmentApi.start();
        set((s) => {
          s.sessionId = session.id;
          s.questions = questions;
          s.currentIndex = 0;
          s.responses = {};
          s.step = "questions";
          s.isLoading = false;
        });
      } catch (err) {
        set((s) => {
          s.error =
            err instanceof Error ? err.message : "Failed to start assessment";
          s.isLoading = false;
        });
        throw err;
      }
    },

    answerQuestion: (questionId, value) => {
      set((s) => {
        s.responses[questionId] = value;
      });
    },

    goToNext: () => {
      set((s) => {
        if (s.currentIndex < s.questions.length - 1) {
          s.currentIndex += 1;
        }
      });
    },

    goToPrev: () => {
      set((s) => {
        if (s.currentIndex > 0) {
          s.currentIndex -= 1;
        }
      });
    },

    submitAssessment: async () => {
      const { sessionId, responses } = get();
      if (!sessionId) return;

      set((s) => {
        s.isLoading = true;
        s.error = null;
      });

      try {
        const { results } = await assessmentApi.submit({
          session_id: sessionId,
          responses,
        });
        set((s) => {
          s.results = results;
          s.step = "results";
          s.isLoading = false;
        });
      } catch (err) {
        set((s) => {
          s.error =
            err instanceof Error ? err.message : "Failed to submit assessment";
          s.isLoading = false;
        });
        throw err;
      }
    },

    resetAssessment: () => {
      set(INITIAL_STATE);
    },

    clearError: () => {
      set((s) => {
        s.error = null;
      });
    },

    progress: () => {
      const { questions, responses } = get();
      if (questions.length === 0) return 0;
      return Math.round((Object.keys(responses).length / questions.length) * 100);
    },

    canGoNext: () => {
      const { questions, currentIndex, responses } = get();
      const current = questions[currentIndex];
      return current !== undefined && responses[current.id] !== undefined;
    },

    canSubmit: () => {
      const { questions, responses } = get();
      return (
        questions.length > 0 &&
        questions.every((q) => responses[q.id] !== undefined)
      );
    },
  })),
);
