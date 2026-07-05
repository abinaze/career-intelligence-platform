import { DashboardOverview } from "@/features/dashboard/components/DashboardOverview";

export default function DashboardPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Dashboard</h1>
        <p className="text-muted-foreground">
          Welcome back. Here&apos;s your career intelligence summary.
        </p>
      </div>
      <DashboardOverview />
    </div>
  );
}
