"use client";

import { useEffect, useState } from "react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { Check, Loader2, LogOut } from "lucide-react";
import { cn } from "@/lib/utils";
import { useStorageProvider } from "../hooks/useStorageProvider";
import { describeMigration } from "../lib/migrateProviderData";
import { oneDriveOAuthApi } from "../api/oneDriveOAuth.api";
import {
  clearOneDriveTokens,
  isOneDriveConnected,
  setOneDriveTokens,
} from "../adapters/oneDriveTokens";

type ConnectionState = "checking" | "not_connected" | "connecting" | "claiming" | "connected";

const ERROR_MESSAGES: Record<string, string> = {
  access_denied: "You declined the OneDrive permission request.",
  missing_code_or_state: "Microsoft's response was missing required information. Please try again.",
  invalid_or_expired_ticket: "That connection attempt expired. Please try connecting again.",
  token_exchange_failed: "OneDrive couldn't finish connecting. Please try again.",
  token_exchange_timeout: "Connecting to OneDrive timed out. Please try again.",
  malformed_token_response: "OneDrive returned an unexpected response. Please try again.",
};

function friendlyError(code: string): string {
  return ERROR_MESSAGES[code] ?? "Something went wrong connecting OneDrive. Please try again.";
}

/**
 * OneDrive connect/disconnect panel. Same structure as
 * GoogleDriveConnect.tsx, with one real difference: disconnecting here
 * never calls the backend — there's no `/storage/onedrive/disconnect`
 * endpoint, because Microsoft has no simple per-token revoke API for
 * this flow (see docs/architecture/byos.md). "Disconnect" just clears
 * the locally-stored tokens; a user who wants to fully revoke access
 * needs to do that from their Microsoft account's app permissions page.
 *
 * Always rendered in StorageSettings regardless of the active provider,
 * so it can pick up the post-redirect landing (`onedrive_exchange` /
 * `onedrive_error`) on any render.
 */
export function OneDriveConnect() {
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
    params.delete("onedrive_exchange");
    params.delete("onedrive_error");
    router.replace(`${pathname}?${params.toString()}`);
  }

  useEffect(() => {
    const exchangeCode = searchParams.get("onedrive_exchange");
    const errorCode = searchParams.get("onedrive_error");

    async function syncFromExistingTokens(): Promise<void> {
      setState((await isOneDriveConnected()) ? "connected" : "not_connected");
    }

    async function claim(code: string): Promise<void> {
      setState("claiming");
      try {
        const tokens = await oneDriveOAuthApi.claimExchange(code);
        await setOneDriveTokens(tokens);
        const migration = await selectProvider("onedrive", { fromConnectFlow: true });
        setMigrationNote(describeMigration(migration));
        setState("connected");
      } catch {
        setError(
          "OneDrive connected, but we couldn't finish saving the connection. Please try again.",
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
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [searchParams.get("onedrive_exchange"), searchParams.get("onedrive_error")]);

  async function handleConnect(): Promise<void> {
    setError(null);
    setState("connecting");
    try {
      const authorizeUrl = await oneDriveOAuthApi.getAuthorizeUrl();
      window.location.href = authorizeUrl;
    } catch {
      setError("Couldn't start the OneDrive connection. Please try again.");
      setState("not_connected");
    }
  }

  async function handleDisconnect(): Promise<void> {
    setIsDisconnecting(true);
    try {
      // No backend call here — see the module docstring above for why.
      await clearOneDriveTokens();
      if (provider === "onedrive") {
        await selectProvider("platform");
      }
      setState("not_connected");
    } finally {
      setIsDisconnecting(false);
    }
  }

  if (state === "checking" || state === "claiming") {
    return (
      <div className="text-muted-foreground flex items-center gap-2 rounded-lg border p-4 text-xs">
        <Loader2 className="h-3.5 w-3.5 animate-spin" />
        {state === "claiming" ? "Finishing OneDrive connection…" : "Checking OneDrive status…"}
      </div>
    );
  }

  return (
    <div className="space-y-2 rounded-lg border p-4">
      <div className="flex items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <span className="text-lg leading-none">☁️</span>
          <span className="text-sm font-semibold">Microsoft OneDrive</span>
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
            {state === "connecting" ? "Redirecting to Microsoft…" : "Connect OneDrive"}
          </button>
        )}
      </div>

      <p className="text-muted-foreground text-xs">
        {state === "connected"
          ? "Your career data is stored in a private, hidden file in your own OneDrive."
          : "Connect your OneDrive to store your career data there instead of on our servers."}
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
