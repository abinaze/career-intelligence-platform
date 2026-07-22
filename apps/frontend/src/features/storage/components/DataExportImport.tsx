"use client";

import { useRef, useState } from "react";
import { AlertTriangle, Download, Upload } from "lucide-react";
import { cn } from "@/lib/utils";
import { useStorageProvider } from "../hooks/useStorageProvider";
import {
  buildExportFile,
  buildExportFilename,
  describeImportResult,
  downloadJson,
  ImportFileError,
  parseImportFile,
  type CareerDataExportFile,
} from "../lib/exportImportData";

type ImportState = "idle" | "confirming";

/**
 * Manual export/import panel — Phase 9d. Works against whichever
 * provider is currently active (see exportImportData.ts's module
 * docstring for why this isn't a sixth StorageAdapter).
 */
export function DataExportImport() {
  const { providerMeta, adapter } = useStorageProvider();
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [isExporting, setIsExporting] = useState(false);
  const [exportError, setExportError] = useState<string | null>(null);

  const [importState, setImportState] = useState<ImportState>("idle");
  const [isImporting, setIsImporting] = useState(false);
  const [pendingImport, setPendingImport] = useState<CareerDataExportFile | null>(null);
  const [importError, setImportError] = useState<string | null>(null);
  const [importResultMessage, setImportResultMessage] = useState<string | null>(null);

  async function handleExport(): Promise<void> {
    setIsExporting(true);
    setExportError(null);
    try {
      const file = await buildExportFile(adapter);
      downloadJson(buildExportFilename(), file);
    } catch {
      setExportError("Couldn't export your data. Please try again.");
    } finally {
      setIsExporting(false);
    }
  }

  function handleFileSelected(event: React.ChangeEvent<HTMLInputElement>): void {
    const selectedFile = event.target.files?.[0];
    event.target.value = ""; // allow re-selecting the same file later
    if (!selectedFile) return;

    setImportError(null);
    setImportResultMessage(null);

    void selectedFile.text().then((text) => {
      try {
        const parsed = parseImportFile(text);
        setPendingImport(parsed);
        setImportState("confirming");
      } catch (error) {
        setImportError(
          error instanceof ImportFileError
            ? error.message
            : "Couldn't read that file. Please try again.",
        );
      }
    });
  }

  async function handleConfirmImport(): Promise<void> {
    if (!pendingImport) return;
    setIsImporting(true);
    try {
      const result = await adapter.restoreSnapshot(pendingImport.snapshot);
      setImportResultMessage(describeImportResult(result));
    } catch {
      setImportError("Couldn't import that file. Please try again.");
    } finally {
      setPendingImport(null);
      setImportState("idle");
      setIsImporting(false);
    }
  }

  function handleCancelImport(): void {
    setPendingImport(null);
    setImportState("idle");
  }

  return (
    <div className="space-y-3 rounded-lg border p-4">
      <div>
        <p className="text-sm font-semibold">Backup &amp; restore</p>
        <p className="text-muted-foreground mt-0.5 text-xs">
          Download a copy of your profile and assessment as a file, or restore from one you saved
          earlier. Works with whichever storage you&apos;re currently using ({providerMeta.label}).
        </p>
      </div>

      <div className="flex flex-wrap gap-2">
        <button
          type="button"
          onClick={() => void handleExport()}
          disabled={isExporting}
          className={cn(
            "border-border hover:bg-accent flex items-center gap-1.5 rounded-lg border px-3 py-1.5",
            "text-xs font-medium transition-colors disabled:opacity-60",
          )}
        >
          <Download className="h-3.5 w-3.5" />
          {isExporting ? "Exporting…" : "Export data"}
        </button>

        <button
          type="button"
          onClick={() => fileInputRef.current?.click()}
          className={cn(
            "border-border hover:bg-accent flex items-center gap-1.5 rounded-lg border px-3 py-1.5",
            "text-xs font-medium transition-colors",
          )}
        >
          <Upload className="h-3.5 w-3.5" />
          Import data
        </button>
        <input
          ref={fileInputRef}
          type="file"
          accept=".json,application/json"
          onChange={handleFileSelected}
          className="hidden"
        />
      </div>

      {importState === "confirming" && pendingImport && (
        <div className="border-destructive/40 bg-destructive/5 rounded-lg border p-3">
          <div className="flex items-start gap-2">
            <AlertTriangle className="text-destructive mt-0.5 h-3.5 w-3.5 flex-shrink-0" />
            <div className="flex-1">
              <p className="text-destructive text-xs font-medium">
                This will overwrite your current profile and assessment on {providerMeta.label}.
              </p>
              <p className="text-muted-foreground mt-1 text-xs">
                File exported {new Date(pendingImport.exported_at).toLocaleDateString()} from{" "}
                {pendingImport.exported_from}.
              </p>
              <div className="mt-2 flex gap-2">
                <button
                  type="button"
                  onClick={handleCancelImport}
                  className="border-border hover:bg-accent rounded-lg border px-3 py-1.5 text-xs font-medium transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="button"
                  onClick={() => void handleConfirmImport()}
                  disabled={isImporting}
                  className="bg-destructive text-destructive-foreground rounded-lg px-3 py-1.5 text-xs font-medium transition-opacity hover:opacity-90 disabled:opacity-60"
                >
                  Yes, import and overwrite
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {importResultMessage && (
        <p className="rounded-lg border border-emerald-200 bg-emerald-50 px-3 py-2 text-xs text-emerald-800 dark:border-emerald-900 dark:bg-emerald-950/40 dark:text-emerald-300">
          {importResultMessage}
        </p>
      )}

      {(exportError ?? importError) && (
        <p className="rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-xs text-red-800 dark:border-red-900 dark:bg-red-950/40 dark:text-red-300">
          {exportError ?? importError}
        </p>
      )}
    </div>
  );
}
