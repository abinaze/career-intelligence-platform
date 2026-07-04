import { AssessmentFlow } from "@/features/assessment/components/AssessmentFlow";

export default function AssessmentPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Assessment</h1>
        <p className="text-muted-foreground">
          Discover your psychometric profile across 11 career dimensions.
        </p>
      </div>
      <AssessmentFlow />
    </div>
  );
}
