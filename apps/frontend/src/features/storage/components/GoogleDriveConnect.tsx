"use client";

import { useEffect, useState } from "react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { Check, Loader2, LogOut } from "lucide-react";
import { cn } from "@/lib/utils";
import { useStorageProvider } from "../hooks/useStorageProvider";
import { describeMigration } from "../lib/migrateProviderData";
import { googleDriveOAuthApi } from "../api/googleDriveOAuth.api";
import {
  clearGoogleDriveTokens,
  getGoogleDriveTokens,
  isGoogleDriveConnected,
  setGoogleDriveTokens,
} from "../adapters/googleDriveTokens";

type ConnectionState = "checking" | "not_connected" | "connecting" | "claiming" | "connected";

const ERROR_MESSAGES: Record<string, string> = {
  access_denied: "You declined the Google Drive permission request.",
  missing_code_or_state: "Google's response was missing required information. Please try again.",
  invalid_or_expired_ticket: "That connection attempt expired. Please try connecting again.",
  token_exchange_failed: "Google Drive couldn't finish connecting. Please try again.",
  token_exchange_timeout: "Connecting to Google Drive timed out. Please try again.",
  malformed_token_response: "Google Drive returned an unexpected response. Please try again.",
};

function friendlyError(code: string): string {
  return ERROR_MESSAGES[code] ?? "Something went wrong connecting Google Drive. Please try again.";
}

/**
 * Google Drive connect/disconnect panel.
 *
 * Handles both halves of the OAuth flow from the frontend side:
 * - Kicking off a connect attempt (full-page redirect to Google).
 * - Landing back here after the backend's /callback redirect, with
 *   either `gdrive_exchange` or `gdrive_error` in the URL — claims the
 *   staged tokens, stores them, and switches the active storage provider
 *   only once that succeeds (see useStorageProvider.selectProvider).
 *
 * Always rendered in StorageSettings regardless of which provider is
 * currently active, so it can (a) handle the post-redirect landing on
 * any render, and (b) show connect/disconnect status independent of
 * whether Google Drive is the *active* provider yet.
 */
export function GoogleDriveConnect() {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const { provider, selectProvider } = useStorageProvider();

  const [state, setState] = useState<ConnectionState>("checking");
  const [error, setError] = useState<string | null>(null);
  const [isDisconnecting, setIsDisconnecting] = useState(false);
  const [migrationNote, setMigrationNote] = useState<string | null>(null);

  function clearRedirectParams(): void {
    const params = new URLSearchParams(searchParams.toString());
    params.delete("gdrive_exchange");
    params.delete("gdrive_error");
    router.replace(`${pathname}?${params.toString()}`);
  }

  useEffect(() => {
    const exchangeCode = searchParams.get("gdrive_exchange");
    const errorCode = searchParams.get("gdrive_error");

    async function syncFromExistingTokens(): Promise<void> {
      setState((await isGoogleDriveConnected()) ? "connected" : "not_connected");
    }

    async function claim(code: string): Promise<void> {
      setState("claiming");
      try {
        const tokens = await googleDriveOAuthApi.claimExchange(code);
        await setGoogleDriveTokens(tokens);
        const migration = await selectProvider("google_drive", { fromConnectFlow: true });
        setMigrationNote(describeMigration(migration));
        setState("connected");
      } catch {
        setError(
          "Google Drive connected, but we couldn't finish saving the connection. Please try again.",
        );
        await syncFromExistingTokens();
      } finally {
        clearRedirectParams();
      }
    }

    async function handleErrorRedirect(code: string): Promise<void> {
      setError(friendlyError(code));
      clearRedirectParams();
      await syncFromExistingTokens();
    }

    if (exchangeCode) {
      void claim(exchangeCode);
    } else if (errorCode) {
      void handleErrorRedirect(errorCode);
    } else {
      void syncFromExistingTokens();
    }
    // Only re-run when the redirect params themselves change, not on
    // every searchParams identity change from clearRedirectParams()'s
    // own router.replace().
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [searchParams.get("gdrive_exchange"), searchParams.get("gdrive_error")]);

  async function handleConnect(): Promise<void> {
    setError(null);
    setState("connecting");
    try {
      const authorizeUrl = await googleDriveOAuthApi.getAuthorizeUrl();
      window.location.href = authorizeUrl;
    } catch {
      setError("Couldn't start the Google Drive connection. Please try again.");
      setState("not_connected");
    }
  }

  async function handleDisconnect(): Promise<void> {
    setIsDisconnecting(true);
    try {
      const tokens = await getGoogleDriveTokens();
      if (tokens) {
        await googleDriveOAuthApi.disconnect(tokens.access_token).catch(() => undefined);
      }
    } finally {
      await clearGoogleDriveTokens();
      if (provider === "google_drive") {
        await selectProvider("platform");
      }
      setState("not_connected");
      setIsDisconnecting(false);
    }
  }

  if (state === "checking" || state === "claiming") {
    return (
      <div className="text-muted-foreground flex items-center gap-2 rounded-lg border p-4 text-xs">
        <Loader2 className="h-3.5 w-3.5 animate-spin" />
        {state === "claiming"
          ? "Finishing Google Drive connection…"
          : "Checking Google Drive status…"}
      </div>
    );
  }

  return (
    <div className="space-y-2 rounded-lg border p-4">
      <div className="flex items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <span className="text-lg leading-none">☁️</span>
          <span className="text-sm font-semibold">Google Drive</span>
          {state === "connected" && (
            <span className="flex items-center gap-1 rounded-full bg-emerald-100 px-2 py-0.5 text-[10px] font-medium text-emerald-700 dark:bg-emerald-950/40 dark:text-emerald-400">
              <Check className="h-3 w-3" /> Connected
            </span>
          )}
        </div>

        {state === "connected" ? (
          <button
            type="button"
            onClick={() => void handleDisconnect()}
            disabled={isDisconnecting}
            className={cn(
              "border-border hover:bg-accent flex items-center gap-1.5 rounded-lg border px-3 py-1.5",
              "text-xs font-medium transition-colors disabled:opacity-60",
            )}
          >
            {isDisconnecting ? (
              <Loader2 className="h-3.5 w-3.5 animate-spin" />
            ) : (
              <LogOut className="h-3.5 w-3.5" />
            )}
            Disconnect
          </button>
        ) : (
          <button
            type="button"
            onClick={() => void handleConnect()}
            disabled={state === "connecting"}
            className={cn(
              "bg-primary text-primary-foreground rounded-lg px-3 py-1.5",
              "text-xs font-medium transition-opacity hover:opacity-90 disabled:opacity-60",
            )}
          >
            {state === "connecting" ? "Redirecting to Google…" : "Connect Google Drive"}
          </button>
        )}
      </div>

      <p className="text-muted-foreground text-xs">
        {state === "connected"
          ? "Your career data is stored in a private, hidden file in your own Google Drive."
          : "Connect your Google Drive to store your career data there instead of on our servers."}
      </p>

      {migrationNote && (
        <p className="rounded-lg border border-emerald-200 bg-emerald-50 px-3 py-2 text-xs text-emerald-800 dark:border-emerald-900 dark:bg-emerald-950/40 dark:text-emerald-300">
          {migrationNote}
        </p>
      )}

      {error && (
        <p className="rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-xs text-red-800 dark:border-red-900 dark:bg-red-950/40 dark:text-red-300">
          {error}
        </p>
      )}
    </div>
  );
}
