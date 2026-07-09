"use client";

import { useState, useRef } from "react";
import { Send } from "lucide-react";
import { cn } from "@/lib/utils";

interface ChatInputProps {
  onSend: (message: string) => void;
  disabled?: boolean;
}

const SUGGESTIONS = [
  "What careers match my profile?",
  "How do I transition into tech?",
  "What skills should I develop?",
  "How do I negotiate salary?",
];

export function ChatInput({ onSend, disabled = false }: ChatInputProps) {
  const [value, setValue] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  function handleSend() {
    const trimmed = value.trim();
    if (!trimmed || disabled) return;
    onSend(trimmed);
    setValue("");
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
    }
  }

  function handleKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  }

  function handleInput(e: React.ChangeEvent<HTMLTextAreaElement>) {
    setValue(e.target.value);
    // Auto-resize textarea
    const el = e.target;
    el.style.height = "auto";
    el.style.height = `${Math.min(el.scrollHeight, 160)}px`;
  }

  function handleSuggestion(text: string) {
    setValue(text);
    textareaRef.current?.focus();
  }

  return (
    <div className="space-y-2">
      {/* Suggestion chips — only shown when input is empty */}
      {!value && (
        <div className="flex flex-wrap gap-1.5">
          {SUGGESTIONS.map((s) => (
            <button
              key={s}
              onClick={() => handleSuggestion(s)}
              disabled={disabled}
              className={cn(
                "rounded-full border border-border bg-card px-3 py-1 text-xs",
                "text-muted-foreground transition-colors",
                "hover:border-primary/50 hover:text-primary",
                "disabled:cursor-not-allowed disabled:opacity-50",
              )}
            >
              {s}
            </button>
          ))}
        </div>
      )}

      {/* Input row */}
      <div className="flex items-end gap-2 rounded-xl border border-input bg-background p-2">
        <textarea
          ref={textareaRef}
          rows={1}
          value={value}
          onChange={handleInput}
          onKeyDown={handleKeyDown}
          disabled={disabled}
          placeholder="Ask your career counsellor anything…"
          className={cn(
            "flex-1 resize-none bg-transparent px-2 py-1 text-sm",
            "placeholder:text-muted-foreground",
            "focus:outline-none",
            "disabled:cursor-not-allowed disabled:opacity-50",
            "max-h-40 overflow-y-auto",
          )}
        />
        <button
          onClick={handleSend}
          disabled={disabled || !value.trim()}
          className={cn(
            "flex h-8 w-8 flex-shrink-0 items-center justify-center",
            "rounded-lg bg-primary text-primary-foreground",
            "transition-opacity hover:opacity-90",
            "disabled:cursor-not-allowed disabled:opacity-40",
          )}
        >
          <Send className="h-3.5 w-3.5" />
        </button>
      </div>
      <p className="text-center text-[10px] text-muted-foreground">
        Shift+Enter for new line · Enter to send
      </p>
    </div>
  );
}
