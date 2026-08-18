"use client";

import { useEffect, useState } from "react";
import { Check, Eye, EyeOff, Loader2, Trash2 } from "lucide-react";
import { cn } from "@/lib/utils";
import { aiProvidersApi } from "../api/aiProviders.api";
import {
  clearAnthropicByoKey,
  getAnthropicByoKey,
  hasAnthropicByoKey,
  setAnthropicByoKey,
} from "../lib/anthropicKeyStorage";

type ViewState = "checking" | "not_connected" | "editing" | "testing" | "connected";

function maskKey(key: string): string {
  if (key.length <= 8) return "••••••••";
  return `${key.slice(0, 4)}${"•".repeat(8)}${key.slice(-4)}`;
}

/**
 * Anthropic (Claude) BYO-key connect panel.
 *
 * Mirrors the shape of features/storage/components/GoogleDriveConnect.tsx
 * (checking/connected/error states, friendly error messages, a short
 * "what this does" line) but for a pasted-key flow instead of an OAuth
 * redirect — there's no third-party consent screen to send the user to.
 *
 * The key is validated against the backend's one-shot test-connection
 * endpoint *before* being saved, then stored client-side only (see
 * anthropicKeyStorage.ts) — the backend never persists it.
 */
export function AnthropicKeyConnect() {
  const [state, setState] = useState<ViewState>("checking");
  const [inputValue, setInputValue] = useState("");
  const [showInput, setShowInput] = useState(false);
  const [storedKey, setStoredKey] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function load(): Promise<void> {
      const key = await getAnthropicByoKey();
      setStoredKey(key);
      setState(key ? "connected" : "not_connected");
    }
    void load();
  }, []);

  async function handleTestAndSave(): Promise<void> {
    setError(null);
    if (!inputValue.trim()) {
      setError("Enter an API key first.");
      return;
    }
    setState("testing");
    try {
      const result = await aiProvidersApi.testAnthropicKey(inputValue.trim());
      if (!result.success) {
        setError(result.message);
        setState("editing");
        return;
      }
      await setAnthropicByoKey(inputValue.trim());
      setStoredKey(inputValue.trim());
      setInputValue("");
      setShowInput(false);
      setState("connected");
    } catch {
      setError("Couldn't reach the server to test this key. Please try again.");
      setState("editing");
    }
  }

  async function handleRemove(): Promise<void> {
    await clearAnthropicByoKey();
    setStoredKey(null);
    setState((await hasAnthropicByoKey()) ? "connected" : "not_connected");
  }

  if (state === "checking") {
    return (
      <div className="text-muted-foreground flex items-center gap-2 rounded-lg border p-4 text-xs">
        <Loader2 className="h-3.5 w-3.5 animate-spin" />
        Checking your Anthropic key…
      </div>
    );
  }

  return (
    <div className="space-y-2 rounded-lg border p-4">
      <div className="flex items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <span className="text-lg leading-none">🤖</span>
          <span className="text-sm font-semibold">Anthropic (Claude)</span>
          {state === "connected" && (
            <span className="flex items-center gap-1 rounded-full bg-emerald-100 px-2 py-0.5 text-[10px] font-medium text-emerald-700 dark:bg-emerald-950/40 dark:text-emerald-400">
              <Check className="h-3 w-3" /> Connected
            </span>
          )}
        </div>

        {state === "connected" && (
          <button
            type="button"
            onClick={() => void handleRemove()}
            className={cn(
              "border-border hover:bg-accent flex items-center gap-1.5 rounded-lg border px-3 py-1.5",
              "text-xs font-medium transition-colors",
            )}
          >
            <Trash2 className="h-3.5 w-3.5" />
            Remove
          </button>
        )}

        {state === "not_connected" && (
          <button
            type="button"
            onClick={() => setState("editing")}
            className="bg-primary text-primary-foreground rounded-lg px-3 py-1.5 text-xs font-medium transition-opacity hover:opacity-90"
          >
            Connect your own key
          </button>
        )}
      </div>

      <p className="text-muted-foreground text-xs">
        {state === "connected"
          ? "Chat uses your own Anthropic key. It's stored only in this browser and sent directly with your chat requests — never saved on our servers."
          : "Connect your own Anthropic API key so chat uses your account instead of ours. Get one at console.anthropic.com."}
      </p>

      {state === "connected" && storedKey && (
        <p className="text-muted-foreground bg-secondary/50 rounded-md px-2 py-1 font-mono text-xs">
          {maskKey(storedKey)}
        </p>
      )}

      {(state === "editing" || state === "testing") && (
        <div className="space-y-2 pt-1">
          <div className="relative">
            <input
              type={showInput ? "text" : "password"}
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              placeholder="sk-ant-…"
              disabled={state === "testing"}
              className={cn(
                "border-border bg-background w-full rounded-lg border px-3 py-2 pr-9",
                "focus:ring-primary font-mono text-xs focus:ring-1 focus:outline-none",
                "disabled:opacity-60",
              )}
            />
            <button
              type="button"
              onClick={() => setShowInput((v) => !v)}
              className="text-muted-foreground hover:text-foreground absolute top-1/2 right-2 -translate-y-1/2"
              tabIndex={-1}
            >
              {showInput ? <EyeOff className="h-3.5 w-3.5" /> : <Eye className="h-3.5 w-3.5" />}
            </button>
          </div>

          <div className="flex gap-2">
            <button
              type="button"
              onClick={() => {
                setState("not_connected");
                setInputValue("");
                setError(null);
              }}
              disabled={state === "testing"}
              className="border-border hover:bg-accent rounded-lg border px-3 py-1.5 text-xs font-medium transition-colors disabled:opacity-60"
            >
              Cancel
            </button>
            <button
              type="button"
              onClick={() => void handleTestAndSave()}
              disabled={state === "testing"}
              className={cn(
                "bg-primary text-primary-foreground flex items-center gap-1.5 rounded-lg px-3 py-1.5",
                "text-xs font-medium transition-opacity hover:opacity-90 disabled:opacity-60",
              )}
            >
              {state === "testing" && <Loader2 className="h-3.5 w-3.5 animate-spin" />}
              {state === "testing" ? "Testing…" : "Test & save"}
            </button>
          </div>
        </div>
      )}

      {error && (
        <p className="rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-xs text-red-800 dark:border-red-900 dark:bg-red-950/40 dark:text-red-300">
          {error}
        </p>
      )}
    </div>
  );
}
