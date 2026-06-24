export default function AssessmentPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Assessment</h1>
        <p className="text-muted-foreground">
          Discover your psychometric profile across 11 career dimensions.
        </p>
      </div>
      <div className="rounded-xl border bg-card p-8 text-center shadow-sm">
        <h2 className="text-xl font-semibold">Ready to begin?</h2>
        <p className="mt-2 text-muted-foreground max-w-md mx-auto">
          This assessment takes approximately 10 minutes and measures your
          Big Five personality traits and RIASEC vocational interests.
        </p>
        <button className="mt-6 rounded-lg bg-primary px-6 py-2.5 text-sm font-medium text-primary-foreground hover:bg-primary/90 transition-colors">
          Start Assessment
        </button>
      </div>
    </div>
  );
}
