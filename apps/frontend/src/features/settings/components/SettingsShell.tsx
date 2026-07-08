"use client";

import { useState } from "react";
import { cn } from "@/lib/utils";
import { ProfileForm } from "./ProfileForm";
import { AccountForm } from "./AccountForm";
import { ChangePasswordForm } from "./ChangePasswordForm";
import { DangerZone } from "./DangerZone";

const TABS = [
  { id: "profile", label: "Profile" },
  { id: "account", label: "Account" },
  { id: "password", label: "Password" },
  { id: "danger", label: "Danger zone" },
] as const;

type TabId = (typeof TABS)[number]["id"];

const SECTION_META: Record<TabId, { title: string; description: string }> = {
  profile: {
    title: "Career profile",
    description:
      "Tell us about your background. A complete profile improves recommendation accuracy.",
  },
  account: {
    title: "Account details",
    description: "Your name and email address associated with this account.",
  },
  password: {
    title: "Change password",
    description:
      "Update your password. You'll need your current password to make changes.",
  },
  danger: {
    title: "Danger zone",
    description:
      "Irreversible actions. Please read carefully before proceeding.",
  },
};

export function SettingsShell() {
  const [activeTab, setActiveTab] = useState<TabId>("profile");
  const meta = SECTION_META[activeTab];

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      {/* Tab bar */}
      <div className="flex gap-1 overflow-x-auto rounded-xl border bg-card p-1 shadow-sm">
        {TABS.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={cn(
              "flex-shrink-0 rounded-lg px-4 py-2 text-sm font-medium transition-colors",
              activeTab === tab.id
                ? "bg-primary text-primary-foreground"
                : "text-muted-foreground hover:bg-accent hover:text-accent-foreground",
              tab.id === "danger" &&
                activeTab !== "danger" &&
                "hover:text-destructive",
              tab.id === "danger" && activeTab === "danger" && "bg-destructive",
            )}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Section content */}
      <div className="rounded-xl border bg-card p-6 shadow-sm">
        <div className="mb-6 border-b pb-4">
          <h2 className="text-base font-semibold">{meta.title}</h2>
          <p className="mt-1 text-sm text-muted-foreground">
            {meta.description}
          </p>
        </div>

        {activeTab === "profile" && <ProfileForm />}
        {activeTab === "account" && <AccountForm />}
        {activeTab === "password" && <ChangePasswordForm />}
        {activeTab === "danger" && <DangerZone />}
      </div>
    </div>
  );
}
