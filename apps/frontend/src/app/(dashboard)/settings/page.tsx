import { SettingsShell } from "@/features/settings/components/SettingsShell";

export default function SettingsPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Settings</h1>
        <p className="text-muted-foreground">
          Manage your profile, account, and preferences.
        </p>
      </div>
      <SettingsShell />
    </div>
  );
}
