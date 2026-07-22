/**
 * Storage feature types.
 *
 * Defines the storage-provider abstraction that lets a user choose where
 * their career and psychometric data lives. See docs/architecture/byos.md
 * for the full design.
 */

import type { DimensionScore, StartAssessmentResponse } from "@/features/assessment/types";
import type { ProfileUpdate, RecommendationResult, UserProfile } from "@/features/careers/types";

// ── Provider catalog ──────────────────────────────────────────────────────────

export type StorageProviderId =
  "platform" | "local_device" | "google_drive" | "onedrive" | "dropbox" | "local_folder";

export type StorageProviderAvailability = "available" | "coming_soon";

export interface StorageProviderMeta {
  id: StorageProviderId;
  label: string;
  description: string;
  icon: string; // emoji, matches the plain-text onboarding copy style
  availability: StorageProviderAvailability;
}

export const STORAGE_PROVIDERS: StorageProviderMeta[] = [
  {
    id: "platform",
    label: "Your Account (Default)",
    description: "Store your data with your account, the way most apps work today.",
    icon: "🔐",
    availability: "available",
  },
  {
    id: "local_device",
    label: "This Device (Private)",
    description:
      "Store your data only on this device using secure browser storage. Never leaves your device.",
    icon: "🖥️",
    availability: "available",
  },
  {
    id: "google_drive",
    label: "Google Drive",
    description: "Store your data securely in your Google Drive account.",
    icon: "☁️",
    availability: "available",
  },
  {
    id: "onedrive",
    label: "Microsoft OneDrive",
    description: "Store your data securely in your Microsoft OneDrive account.",
    icon: "☁️",
    availability: "available",
  },
  {
    id: "dropbox",
    label: "Dropbox",
    description: "Store your data securely in your Dropbox account.",
    icon: "📦",
    availability: "available",
  },
  {
    id: "local_folder",
    label: "Local Folder",
    description:
      "Store your data as files on your computer and import or export them whenever you need.",
    icon: "💾",
    availability: "coming_soon",
  },
];

// ── Local data shapes ──────────────────────────────────────────────────────────
// Structurally identical to the backend/platform shapes so the same UI
// components work regardless of which adapter is active.

export type LocalUserProfile = UserProfile;

export interface LocalAssessmentResults {
  session_id: string;
  assessment_type: string;
  completed_at: string;
  dimension_scores: DimensionScore[];
  model_version: string;
}

/**
 * Shape of the single JSON file GoogleDriveAdapter reads/writes in the
 * user's Drive appDataFolder (career-intelligence-data.json). Mirrors
 * what LocalDeviceAdapter keeps across three separate IndexedDB keys,
 * combined into one file since Drive storage is file-based rather than
 * key-based.
 */
export interface GoogleDriveFileContents {
  profile: UserProfile | null;
  assessment: LocalAssessmentResults | null;
  recommendations: RecommendationResult | null;
  updated_at: string;
}

/**
 * Shape of the single JSON file OneDriveAdapter reads/writes in the
 * user's OneDrive app folder (career-intelligence-data.json). Same
 * fields as GoogleDriveFileContents — kept as a separate type rather
 * than reused, matching this project's existing norm of small,
 * intentional duplication across adapter implementations (see the
 * profile-completeness weighting duplicated in each adapter).
 */
export interface OneDriveFileContents {
  profile: UserProfile | null;
  assessment: LocalAssessmentResults | null;
  recommendations: RecommendationResult | null;
  updated_at: string;
}

/**
 * Shape of the single JSON file DropboxAdapter reads/writes at
 * /career-intelligence-data.json within the app's sandboxed "App folder"
 * space. Same fields as GoogleDriveFileContents/OneDriveFileContents —
 * kept separate rather than shared, matching this project's existing
 * norm of small, intentional duplication across adapter implementations.
 */
export interface DropboxFileContents {
  profile: UserProfile | null;
  assessment: LocalAssessmentResults | null;
  recommendations: RecommendationResult | null;
  updated_at: string;
}

// ── Migration (Phase 9e) ────────────────────────────────────────────────────

/**
 * Portable snapshot of a user's data, used to move it from one storage
 * adapter to another when switching providers (see
 * features/storage/lib/migrateProviderData.ts).
 *
 * Deliberately excludes recommendations: they're a derived cache with no
 * independent value — recomputable for free from the assessment via
 * getRecommendations() — and none of the five adapters expose a raw
 * "read the cached value without recomputing" getter, so including them
 * here would mean adding a new method to every adapter purely to save
 * one backend round-trip after a rare, deliberate action.
 */
export interface StorageSnapshot {
  profile: UserProfile | null;
  assessment: LocalAssessmentResults | null;
}

/**
 * What actually got restored. Not just a success/failure flag — some
 * adapters can only partially restore a snapshot (see PlatformAdapter,
 * which has no backend endpoint to set a precomputed assessment result
 * directly). Callers should use this to tell the user the truth rather
 * than assume a migration was complete.
 */
export interface RestoreSnapshotResult {
  profileRestored: boolean;
  assessmentRestored: boolean;
}

// ── Storage adapter interface ─────────────────────────────────────────────────

export interface StorageAdapter {
  readonly providerId: StorageProviderId;

  getProfile(): Promise<UserProfile | null>;
  saveProfile(updates: ProfileUpdate): Promise<UserProfile>;

  startAssessment(assessmentType?: string): Promise<StartAssessmentResponse>;
  submitAssessment(
    sessionId: string,
    responses: Record<string, number>,
  ): Promise<{ session: unknown; results: LocalAssessmentResults }>;
  getLatestAssessmentResults(): Promise<LocalAssessmentResults | null>;

  getRecommendations(topK?: number): Promise<RecommendationResult>;

  /** Read this adapter's data as a portable snapshot, for migration to another adapter. */
  exportSnapshot(): Promise<StorageSnapshot>;
  /** Write a snapshot exported from another adapter into this one. See RestoreSnapshotResult. */
  restoreSnapshot(snapshot: StorageSnapshot): Promise<RestoreSnapshotResult>;

  /** Permanently erase all data held by this adapter. Irreversible. */
  clearAll(): Promise<void>;
}
