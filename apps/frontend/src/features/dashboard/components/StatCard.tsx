"use client";

import Link from "next/link";
import { cn } from "@/lib/utils";

interface StatCardProps {
  label: string;
  value: string;
  sub: string;
  href?: string;
  loading?: boolean;
  accent?: boolean;
}

export function StatCard({
  label,
  value,
  sub,
  href,
  loading = false,
  accent = false,
}: StatCardProps) {
  const inner = (
    <div
      className={cn(
        "rounded-xl border bg-card p-6 shadow-sm transition-shadow",
        href && "cursor-pointer hover:shadow-md",
        accent && "border-primary/30 bg-primary/5",
      )}
    >
      <p className="text-sm font-medium text-muted-foreground">{label}</p>
      {loading ? (
        <div className="mt-2 h-8 w-24 animate-pulse rounded bg-secondary" />
      ) : (
        <p className={cn("mt-2 text-2xl font-bold", accent && "text-primary")}>
          {value}
        </p>
      )}
      <p className="mt-1 text-xs text-muted-foreground">{sub}</p>
    </div>
  );

  if (href) return <Link href={href}>{inner}</Link>;
  return inner;
}
