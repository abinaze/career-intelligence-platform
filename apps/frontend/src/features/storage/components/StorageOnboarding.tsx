"use client";

import { useState } from "react";
import { Check, Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";
import { useStorageProvider } from "../hooks/useStorageProvider";
import { describeMigration } from "../lib/migrateProviderData";
import type { StorageProviderId } from "../types";

interface StorageOnboardingProps {
  /** Called after a provider is successfully selected. */
  onSelected?: (provider: StorageProviderId) => void;
  /** Compact mode drops the header copy — used when embedded in Settings. */
  compact?: boolean;
}

export function StorageOnboarding({ onSelected, compact = false }: StorageOnboardingProps) {
  const { provider, providers, selectProvider } = useStorageProvider();
  const [pending, setPending] = useState<StorageProviderId | null>(null);
  const [migrationNote, setMigrationNote] = useState<string | null>(null);

  async function handleSelect(id: StorageProviderId): Promise<void> {
    setPending(id);
    setMigrationNote(null);
    const migration = await selectProvider(id);
    setPending(null);
    setMigrationNote(describeMigration(migration));
    onSelected?.(id);
  }

  return (
    <div className="space-y-6">
      {!compact && (
        <div>
          <h2 className="text-xl font-bold">Choose Your Storage Location</h2>
          <p className="text-muted-foreground mt-1 text-sm">
            Your career data belongs to you. Career Intelligence does not store your personal career
            data on its own servers by default — you choose where your information is stored, and
            you can change your storage provider at any time.
          </p>
        </div>
      )}

      <div className="grid gap-3 sm:grid-cols-2">
        {providers.map((p) => {
          const isActive = p.id === provider;
          const isComingSoon = p.availability === "coming_soon";
          // google_drive, onedrive, and dropbox are genuinely available,
          // but can't be switched to by a plain picker click — they need
          // the OAuth connect flow below (see
          // useStorageProvider.selectProvider). Distinguish this from
          // "coming soon" rather than lumping them together, since the
          // underlying reason and the copy shown are different.
          const needsConnect =
            (p.id === "google_drive" || p.id === "onedrive" || p.id === "dropbox") && !isActive;
          const isPending = pending === p.id;

          return (
            <button
              key={p.id}
              type="button"
              disabled={isComingSoon || needsConnect}
              onClick={() => void handleSelect(p.id)}
              className={cn(
                "flex items-start gap-3 rounded-xl border p-4 text-left transition-colors",
                isActive
                  ? "border-primary bg-primary/5"
                  : "border-border bg-card hover:border-primary/40",
                (isComingSoon || needsConnect) && "cursor-not-allowed opacity-60",
              )}
            >
              <span className="text-2xl leading-none">{p.icon}</span>
              <div className="min-w-0 flex-1">
                <div className="flex items-center gap-2">
                  <span className="text-sm font-semibold">{p.label}</span>
                  {isComingSoon && (
                    <span className="bg-secondary text-muted-foreground rounded-full px-2 py-0.5 text-[10px] font-medium">
                      Coming soon
                    </span>
                  )}
                  {needsConnect && (
                    <span className="bg-secondary text-muted-foreground rounded-full px-2 py-0.5 text-[10px] font-medium">
                      Connect below ↓
                    </span>
                  )}
                  {isActive && <Check className="text-primary h-3.5 w-3.5 flex-shrink-0" />}
                </div>
                <p className="text-muted-foreground mt-0.5 text-xs">{p.description}</p>
              </div>
              {isPending && <Loader2 className="text-primary h-4 w-4 flex-shrink-0 animate-spin" />}
            </button>
          );
        })}
      </div>

      <div className="bg-secondary/50 rounded-lg p-4">
        <p className="text-muted-foreground text-xs font-semibold tracking-wide uppercase">
          Privacy Promise
        </p>
        <ul className="text-muted-foreground mt-2 space-y-1 text-xs">
          <li>• Your career data belongs to you.</li>
          <li>
            • When you choose a storage option other than your account, your personal data is never
            stored in Career Intelligence&apos;s own servers.
          </li>
          <li>• You remain in control of your data at all times.</li>
          <li>• You can switch storage providers whenever you choose.</li>
        </ul>
      </div>

      {migrationNote && (
        <p className="rounded-lg border border-emerald-200 bg-emerald-50 px-4 py-3 text-xs text-emerald-800 dark:border-emerald-900 dark:bg-emerald-950/40 dark:text-emerald-300">
          {migrationNote}
        </p>
      )}

      {provider === "local_device" && (
        <p className="rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-xs text-amber-800 dark:border-amber-900 dark:bg-amber-950/40 dark:text-amber-300">
          &quot;This Device&quot; storage does not sync across browsers or devices, and clearing
          your browser data will erase it. Export support is planned for a future update.
        </p>
      )}
    </div>
  );
}
