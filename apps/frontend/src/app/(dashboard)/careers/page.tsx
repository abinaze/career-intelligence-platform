import { CareersList } from "@/features/careers/components/CareersList";

export default function CareersPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Career Matches</h1>
        <p className="text-muted-foreground">
          Personalised recommendations ranked by your psychometric profile.
        </p>
      </div>
      <CareersList />
    </div>
  );
}
