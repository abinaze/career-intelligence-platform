"use client";

import { useState } from "react";
import { AlertTriangle, Trash2 } from "lucide-react";
import { cn } from "@/lib/utils";
import { useStorageProvider } from "@/features/storage/hooks/useStorageProvider";
import { StorageOnboarding } from "@/features/storage/components/StorageOnboarding";

export function StorageSettings() {
  const { provider, providerMeta, adapter } = useStorageProvider();
  const [confirmClear, setConfirmClear] = useState(false);
  const [cleared, setCleared] = useState(false);

  async function handleClear(): Promise<void> {
    await adapter.clearAll();
    setConfirmClear(false);
    setCleared(true);
  }

  return (
    <div className="space-y-6">
      {/* Current provider summary */}
      <div className="bg-secondary/50 flex items-center gap-3 rounded-lg p-4">
        <span className="text-2xl leading-none">{providerMeta.icon}</span>
        <div>
          <p className="text-sm font-semibold">{providerMeta.label}</p>
          <p className="text-muted-foreground text-xs">{providerMeta.description}</p>
        </div>
      </div>

      {/* Provider picker */}
      <StorageOnboarding compact />

      {/* Local-device-only: clear data */}
      {provider === "local_device" && (
        <div className="border-destructive/40 bg-destructive/5 rounded-lg border p-4">
          <div className="flex items-start gap-3">
            <AlertTriangle className="text-destructive mt-0.5 h-4 w-4 flex-shrink-0" />
            <div className="flex-1">
              <p className="text-destructive text-sm font-medium">Clear data on this device</p>
              <p className="text-muted-foreground mt-1 text-xs">
                Permanently erases your locally stored profile, assessment results, and cached
                recommendations from this browser. This cannot be undone and does not affect any
                other storage provider.
              </p>

              {cleared ? (
                <p className="mt-3 text-xs font-medium text-emerald-600 dark:text-emerald-400">
                  ✓ Local data cleared
                </p>
              ) : !confirmClear ? (
                <button
                  onClick={() => setConfirmClear(true)}
                  className={cn(
                    "border-destructive mt-3 rounded-lg border px-3 py-1.5",
                    "text-destructive text-xs font-medium",
                    "hover:bg-destructive hover:text-destructive-foreground transition-colors",
                  )}
                >
                  <Trash2 className="mr-1.5 inline h-3.5 w-3.5" />
                  Clear local data
                </button>
              ) : (
                <div className="mt-3 flex gap-2">
                  <button
                    onClick={() => setConfirmClear(false)}
                    className="border-border hover:bg-accent rounded-lg border px-3 py-1.5 text-xs font-medium transition-colors"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={() => void handleClear()}
                    className="bg-destructive text-destructive-foreground rounded-lg px-3 py-1.5 text-xs font-medium transition-opacity hover:opacity-90"
                  >
                    Yes, clear everything
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
