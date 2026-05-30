import { format, formatDistanceToNow, isValid } from "date-fns";

export function formatDate(
  date: string | Date,
  pattern = "MMM d, yyyy",
): string {
  const d = typeof date === "string" ? new Date(date) : date;
  if (!isValid(d)) return "Invalid date";
  return format(d, pattern);
}

export function formatRelativeTime(date: string | Date): string {
  const d = typeof date === "string" ? new Date(date) : date;
  if (!isValid(d)) return "Unknown";
  return formatDistanceToNow(d, { addSuffix: true });
}

export function formatPercentage(value: number, decimals = 1): string {
  return `${(value * 100).toFixed(decimals)}%`;
}

export function formatScore(score: number, max = 100): string {
  return `${Math.round(score)}/${max}`;
}

export function formatConfidence(confidence: number): string {
  const pct = Math.round(confidence * 100);
  if (pct >= 85) return `${pct}% — High confidence`;
  if (pct >= 65) return `${pct}% — Moderate confidence`;
  return `${pct}% — Exploratory match`;
}

export function truncate(str: string, maxLength: number): string {
  if (str.length <= maxLength) return str;
  return `${str.slice(0, maxLength - 3)}...`;
}

export function capitalize(str: string): string {
  if (!str) return "";
  return str.charAt(0).toUpperCase() + str.slice(1).toLowerCase();
}

export function slugify(str: string): string {
  return str
    .toLowerCase()
    .trim()
    .replace(/[^\w\s-]/g, "")
    .replace(/[\s_-]+/g, "-")
    .replace(/^-+|-+$/g, "");
}
