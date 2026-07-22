"use client";

import { Suspense } from "react";
import { useRouter } from "next/navigation";
import { ArrowRight, Loader2 } from "lucide-react";
import { StorageOnboarding } from "@/features/storage/components/StorageOnboarding";
import { GoogleDriveConnect } from "@/features/storage/components/GoogleDriveConnect";
import { OneDriveConnect } from "@/features/storage/components/OneDriveConnect";
import { DropboxConnect } from "@/features/storage/components/DropboxConnect";

/**
 * Storage onboarding — shown once, immediately after registration (see
 * useAuth.register()). Not a gate: choosing nothing and clicking
 * "Continue" just means the account keeps the default ("Platform")
 * storage, exactly as if this page didn't exist. Returning users never
 * land here again — only a fresh registration redirects here.
 *
 * Renders the same picker + connect panels as Settings → Storage
 * (StorageOnboarding, GoogleDriveConnect, OneDriveConnect,
 * DropboxConnect) rather than a stripped-down subset, so a user who
 * wants to connect a cloud provider right away can actually do the full
 * OAuth round-trip here instead of being told to "do this later in
 * Settings."
 */
export default function StorageOnboardingPage() {
  return (
    <Suspense
      fallback={
        <div className="text-muted-foreground flex items-center gap-2 p-6 text-sm">
          <Loader2 className="h-4 w-4 animate-spin" />
          Loading…
        </div>
      }
    >
      <StorageOnboardingContent />
    </Suspense>
  );
}

function StorageOnboardingContent() {
  const router = useRouter();

  function handleContinue(): void {
    router.push("/dashboard");
  }

  return (
    <div className="mx-auto max-w-2xl space-y-6 py-4">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Where should your data live?</h1>
        <p className="text-muted-foreground mt-1">
          You can change this any time in Settings → Storage.
        </p>
      </div>

      <StorageOnboarding />
      <GoogleDriveConnect />
      <OneDriveConnect />
      <DropboxConnect />

      <div className="flex justify-end">
        <button
          type="button"
          onClick={handleContinue}
          className="bg-primary text-primary-foreground flex items-center gap-1.5 rounded-lg px-4 py-2 text-sm font-medium transition-opacity hover:opacity-90"
        >
          Continue to Dashboard
          <ArrowRight className="h-4 w-4" />
        </button>
      </div>
    </div>
  );
}
