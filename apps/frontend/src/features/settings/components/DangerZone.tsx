"use client";

import { useState } from "react";
import { AlertTriangle, LogOut, Trash2 } from "lucide-react";
import { cn } from "@/lib/utils";
import { useAuth } from "@/features/auth/hooks/useAuth";

export function DangerZone() {
  const { logout } = useAuth();
  const [confirmDelete, setConfirmDelete] = useState(false);

  return (
    <div className="space-y-4">
      {/* Sign out all devices */}
      <div className="flex items-start justify-between gap-4 rounded-lg border border-border p-4">
        <div className="flex items-start gap-3">
          <LogOut className="mt-0.5 h-4 w-4 flex-shrink-0 text-muted-foreground" />
          <div>
            <p className="text-sm font-medium">Sign out of all devices</p>
            <p className="text-xs text-muted-foreground">
              Revokes all active sessions and tokens.
            </p>
          </div>
        </div>
        <button
          onClick={() => void logout()}
          className="flex-shrink-0 rounded-lg border border-border px-3 py-1.5 text-xs font-medium text-muted-foreground transition-colors hover:bg-accent"
        >
          Sign out all
        </button>
      </div>

      {/* Delete account */}
      <div className="rounded-lg border border-destructive/40 bg-destructive/5 p-4">
        <div className="flex items-start gap-3">
          <AlertTriangle className="mt-0.5 h-4 w-4 flex-shrink-0 text-destructive" />
          <div className="flex-1">
            <p className="text-sm font-medium text-destructive">
              Delete account
            </p>
            <p className="mt-1 text-xs text-muted-foreground">
              Permanently deletes your account, profile, assessment history, and
              all associated data. This action cannot be undone.
            </p>
            {!confirmDelete ? (
              <button
                onClick={() => setConfirmDelete(true)}
                className={cn(
                  "mt-3 rounded-lg border border-destructive px-3 py-1.5",
                  "text-xs font-medium text-destructive",
                  "transition-colors hover:bg-destructive hover:text-destructive-foreground",
                )}
              >
                <Trash2 className="mr-1.5 inline h-3.5 w-3.5" />
                Delete my account
              </button>
            ) : (
              <div className="mt-3 space-y-2">
                <p className="text-xs font-medium text-destructive">
                  Are you absolutely sure? This cannot be undone.
                </p>
                <div className="flex gap-2">
                  <button
                    onClick={() => setConfirmDelete(false)}
                    className="rounded-lg border border-border px-3 py-1.5 text-xs font-medium transition-colors hover:bg-accent"
                  >
                    Cancel
                  </button>
                  <button
                    className={cn(
                      "rounded-lg bg-destructive px-3 py-1.5",
                      "text-xs font-medium text-destructive-foreground",
                      "transition-opacity hover:opacity-90",
                    )}
                    onClick={() => {
                      // TODO: wire to DELETE /auth/me when backend endpoint is available
                      setConfirmDelete(false);
                    }}
                  >
                    Yes, permanently delete
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
