import { create } from "zustand";
import { immer } from "zustand/middleware/immer";
import { nanoid } from "nanoid";
import { chatApi } from "../api/chat.api";
import type { ChatMessage, ChatStatus } from "../types";

interface ChatStore {
  messages: ChatMessage[];
  status: ChatStatus;
  error: string | null;

  sendMessage: (content: string) => Promise<void>;
  clearChat: () => void;
  clearError: () => void;
}

const WELCOME_MESSAGE: ChatMessage = {
  id: "welcome",
  role: "assistant",
  content:
    "Hi! I'm your AI career counsellor. I can help you explore careers that match your psychometric profile, prepare for interviews, plan your next move, or answer any career-related questions. What's on your mind?",
  timestamp: new Date(),
};

export const useChatStore = create<ChatStore>()(
  immer((set, get) => ({
    messages: [WELCOME_MESSAGE],
    status: "idle" as ChatStatus,
    error: null,

    sendMessage: async (content: string) => {
      if (!content.trim()) return;

      const userMessage: ChatMessage = {
        id: nanoid(),
        role: "user",
        content: content.trim(),
        timestamp: new Date(),
      };

      set((s) => {
        s.messages.push(userMessage);
        s.status = "loading";
        s.error = null;
      });

      try {
        // Build history from existing messages (excluding welcome + latest user msg)
        const history = get()
          .messages.slice(1, -1) // skip welcome, skip the message we just added
          .map((m) => ({ role: m.role, content: m.content }));

        const response = await chatApi.sendMessage({
          message: content.trim(),
          history,
        });

        const assistantMessage: ChatMessage = {
          id: nanoid(),
          role: "assistant",
          content: response.reply,
          timestamp: new Date(),
        };

        set((s) => {
          s.messages.push(assistantMessage);
          s.status = "idle";
        });
      } catch (err) {
        const errorMessage =
          err instanceof Error ? err.message : "Failed to get a response";
        set((s) => {
          s.status = "error";
          s.error = errorMessage;
          // Add error bubble as assistant message
          s.messages.push({
            id: nanoid(),
            role: "assistant",
            content:
              "Sorry, I couldn't process that right now. Please try again in a moment.",
            timestamp: new Date(),
          });
        });
      }
    },

    clearChat: () => {
      set((s) => {
        s.messages = [{ ...WELCOME_MESSAGE, timestamp: new Date() }];
        s.status = "idle";
        s.error = null;
      });
    },

    clearError: () => {
      set((s) => {
        s.error = null;
        s.status = "idle";
      });
    },
  })),
);
