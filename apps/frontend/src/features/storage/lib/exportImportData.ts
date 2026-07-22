import type {
  RestoreSnapshotResult,
  StorageAdapter,
  StorageProviderId,
  StorageSnapshot,
} from "../types";

/**
 * Manual export/import — Phase 9d.
 *
 * Not a new StorageAdapter (see docs/architecture/byos.md for why
 * "local_folder" stays a `coming_soon` provider rather than becoming a
 * sixth adapter here): this is a provider-agnostic backup/restore
 * feature built entirely on top of the exportSnapshot()/restoreSnapshot()
 * primitives Phase 9e already added to every adapter. Export downloads a
 * JSON file from whichever provider is currently active; import restores
 * a previously-exported file into whichever provider is currently active
 * — same restore semantics as migrateProviderData.ts, including the same
 * one-directional gap for platform storage (see describeImportResult).
 */

export const EXPORT_FORMAT_VERSION = 1;

export interface CareerDataExportFile {
  format_version: number;
  exported_at: string;
  exported_from: StorageProviderId;
  snapshot: StorageSnapshot;
}

/** Reads the given adapter's current data into an export-file-shaped object. Pure — doesn't touch the DOM. */
export async function buildExportFile(adapter: StorageAdapter): Promise<CareerDataExportFile> {
  const snapshot = await adapter.exportSnapshot();
  return {
    format_version: EXPORT_FORMAT_VERSION,
    exported_at: new Date().toISOString(),
    exported_from: adapter.providerId,
    snapshot,
  };
}

/** Triggers a browser download of the given data as a formatted JSON file. Side-effecting; browser-only. */
export function downloadJson(filename: string, data: unknown): void {
  const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}

/** Builds a stable, sortable filename: career-intelligence-data-2026-07-22.json (a numeric suffix is appended on same-day re-export). */
export function buildExportFilename(): string {
  const date = new Date().toISOString().slice(0, 10);
  return `career-intelligence-data-${date}.json`;
}

function isStorageSnapshot(value: unknown): value is StorageSnapshot {
  if (typeof value !== "object" || value === null) return false;
  const v = value as Record<string, unknown>;
  // profile/assessment are only ever null or objects in a real export —
  // this is deliberately shallow (not validating every nested field of
  // UserProfile/LocalAssessmentResults). A malformed inner shape will
  // surface as a clear failure from the adapter's restoreSnapshot() call
  // itself rather than needing to be caught twice.
  const profileOk = v.profile === null || typeof v.profile === "object";
  const assessmentOk = v.assessment === null || typeof v.assessment === "object";
  return "profile" in v && "assessment" in v && profileOk && assessmentOk;
}

export class ImportFileError extends Error {}

/**
 * Parses and structurally validates an export file's text content.
 * Throws ImportFileError with a message safe to show the user directly
 * (not a raw JSON.parse or type-mismatch error) if the file isn't a
 * career-intelligence-platform export at all, or is a version this
 * build doesn't understand.
 */
export function parseImportFile(fileText: string): CareerDataExportFile {
  let parsed: unknown;
  try {
    parsed = JSON.parse(fileText);
  } catch {
    throw new ImportFileError("That file isn't valid JSON.");
  }

  if (typeof parsed !== "object" || parsed === null) {
    throw new ImportFileError("That file doesn't look like a career data export.");
  }
  const obj = parsed as Record<string, unknown>;

  if (typeof obj.format_version !== "number") {
    throw new ImportFileError("That file doesn't look like a career data export.");
  }
  if (obj.format_version > EXPORT_FORMAT_VERSION) {
    throw new ImportFileError(
      "This file was exported by a newer version of the app and can't be imported here.",
    );
  }
  if (!isStorageSnapshot(obj.snapshot)) {
    throw new ImportFileError("That file doesn't look like a career data export.");
  }

  return obj as unknown as CareerDataExportFile;
}

/**
 * Message for the result of an import specifically — wording is
 * deliberately different from migrateProviderData.ts's describeMigration
 * ("moved with you" doesn't fit "I just picked a file off my disk"),
 * even though both wrap the same RestoreSnapshotResult shape.
 */
export function describeImportResult(result: RestoreSnapshotResult): string {
  if (result.profileRestored && result.assessmentRestored) {
    return "Your profile and assessment were restored from the file.";
  }
  if (result.profileRestored && !result.assessmentRestored) {
    // The same one-directional gap as migration — see
    // PlatformAdapter.restoreSnapshot's docstring.
    return "Your profile was restored, but the assessment couldn't be — you'll need to retake it here.";
  }
  if (!result.profileRestored && result.assessmentRestored) {
    return "Your assessment was restored from the file.";
  }
  return "The file didn't contain any profile or assessment data to restore.";
}
