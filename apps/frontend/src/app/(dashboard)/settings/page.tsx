import { Suspense } from "react";
import { Loader2 } from "lucide-react";
import { SettingsShell } from "@/features/settings/components/SettingsShell";

export default function SettingsPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Settings</h1>
        <p className="text-muted-foreground">Manage your profile, account, and preferences.</p>
      </div>
      <Suspense
        fallback={
          <div className="text-muted-foreground flex items-center gap-2 p-6 text-sm">
            <Loader2 className="h-4 w-4 animate-spin" />
            Loading settings…
          </div>
        }
      >
        <SettingsShell />
      </Suspense>
    </div>
  );
}
