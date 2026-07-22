import type { StorageAdapter } from "../types";

/**
 * Moves data from one storage adapter to another ahead of a provider
 * switch, so switching providers doesn't silently strand the user's
 * existing data on the old one. See StorageSnapshot's docstring in
 * ../types for why recommendations aren't part of this.
 *
 * Migrating INTO platform storage from any BYOS adapter has a known,
 * one-directional gap: PlatformAdapter can restore a profile but not an
 * assessment (see PlatformAdapter.restoreSnapshot's docstring) — the
 * `assessmentRestored: false` in the result is not a bug, it's an
 * honest report of what actually happened. Every other direction
 * (platform → BYOS, BYOS → BYOS) restores both fully.
 */
export interface MigrationResult {
  /** False when source and target are the same provider — nothing to do. */
  attempted: boolean;
  profileRestored: boolean;
  assessmentRestored: boolean;
}

export async function migrateStorageData(
  fromAdapter: StorageAdapter,
  toAdapter: StorageAdapter,
): Promise<MigrationResult> {
  if (fromAdapter.providerId === toAdapter.providerId) {
    return { attempted: false, profileRestored: false, assessmentRestored: false };
  }

  let snapshot;
  try {
    snapshot = await fromAdapter.exportSnapshot();
  } catch {
    // The source adapter may already be inaccessible — e.g. this runs
    // during a disconnect flow after tokens were cleared but before the
    // active provider flips back to platform. Migration is a
    // nice-to-have here, not a requirement; don't let it block the
    // provider switch itself.
    return { attempted: false, profileRestored: false, assessmentRestored: false };
  }

  if (snapshot.profile === null && snapshot.assessment === null) {
    // Nothing to migrate (e.g. a brand-new account) — skip the
    // restore call entirely rather than writing a blank snapshot over
    // whatever the target might already have.
    return { attempted: false, profileRestored: false, assessmentRestored: false };
  }

  const result = await toAdapter.restoreSnapshot(snapshot);
  return { attempted: true, ...result };
}

/**
 * Turns a migration result into a short, honest status message for the
 * UI. Shared across StorageOnboarding.tsx and the three *Connect.tsx
 * components so the wording is consistent regardless of which flow
 * triggered the switch. Returns null when there's nothing worth telling
 * the user (nothing was migrated, e.g. a brand-new account).
 */
export function describeMigration(migration: MigrationResult | null): string | null {
  if (!migration?.attempted) return null;

  if (migration.profileRestored && migration.assessmentRestored) {
    return "Your profile and assessment moved with you.";
  }
  if (migration.profileRestored && !migration.assessmentRestored) {
    // The one-directional gap: migrating an assessment INTO platform
    // storage isn't possible yet — see PlatformAdapter.restoreSnapshot.
    return "Your profile moved, but your assessment couldn't be — you'll need to retake it here.";
  }
  if (!migration.profileRestored && migration.assessmentRestored) {
    return "Your assessment moved with you.";
  }
  return null;
}
