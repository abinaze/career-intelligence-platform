"use client";

import { useEffect } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { Loader2, Save } from "lucide-react";
import { cn } from "@/lib/utils";
import { profileSchema, type ProfileSchema } from "@/lib/validations/settings.schemas";
import { useProfile, useUpdateProfile } from "@/features/careers/hooks/useCareers";

const AGE_RANGES = ["Under 18", "18-24", "25-34", "35-44", "45-54", "55-64", "65+"];

const EDUCATION_LEVELS = [
  "High school diploma",
  "Some college",
  "Associate degree",
  "Bachelor's degree",
  "Master's degree",
  "Doctoral degree",
  "Professional degree",
  "Other",
];

const WORK_ENVIRONMENTS = [
  "Remote",
  "Hybrid",
  "On-site",
  "Flexible",
  "Field work",
  "No preference",
];

interface FieldProps {
  label: string;
  error?: string;
  children: React.ReactNode;
  hint?: string;
}

function Field({ label, error, children, hint }: FieldProps) {
  return (
    <div className="space-y-1.5">
      <label className="text-sm font-medium text-foreground">{label}</label>
      {children}
      {hint && !error && (
        <p className="text-xs text-muted-foreground">{hint}</p>
      )}
      {error && <p className="text-xs text-destructive">{error}</p>}
    </div>
  );
}

const inputClass = cn(
  "w-full rounded-lg border border-input bg-background px-3 py-2.5 text-sm",
  "placeholder:text-muted-foreground",
  "focus:outline-none focus:ring-2 focus:ring-ring",
  "disabled:cursor-not-allowed disabled:opacity-50",
);

const selectClass = cn(inputClass, "cursor-pointer");

export function ProfileForm() {
  const { data: profile, isLoading: profileLoading } = useProfile();
  const { mutate: updateProfile, isPending, isSuccess, isError, error } = useUpdateProfile();

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isDirty },
  } = useForm<ProfileSchema>({
    resolver: zodResolver(profileSchema),
    defaultValues: {
      age_range: "",
      education_level: "",
      current_field: "",
      years_of_experience: undefined,
      country: "",
      primary_goal: "",
      desired_work_environment: "",
    },
  });

  // Populate form when profile loads
  useEffect(() => {
    if (profile) {
      reset({
        age_range: profile.age_range ?? "",
        education_level: profile.education_level ?? "",
        current_field: profile.current_field ?? "",
        years_of_experience: profile.years_of_experience ?? undefined,
        country: profile.country ?? "",
        primary_goal: profile.primary_goal ?? "",
        desired_work_environment: profile.desired_work_environment ?? "",
      });
    }
  }, [profile, reset]);

  function onSubmit(values: ProfileSchema) {
    const updates = Object.fromEntries(
      Object.entries(values).filter(([, v]) => v !== "" && v !== undefined),
    );
    updateProfile(updates);
  }

  if (profileLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
      </div>
    );
  }

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-5">
      {/* Profile completeness */}
      {profile && (
        <div className="rounded-lg bg-secondary/50 p-4">
          <div className="mb-2 flex items-center justify-between text-sm">
            <span className="font-medium">Profile completeness</span>
            <span className="text-primary font-semibold">
              {Math.round(profile.completeness_score)}%
            </span>
          </div>
          <div className="h-1.5 w-full overflow-hidden rounded-full bg-secondary">
            <div
              className="h-full rounded-full bg-primary transition-all duration-500"
              style={{ width: `${profile.completeness_score}%` }}
            />
          </div>
          {profile.completeness_score < 80 && (
            <p className="mt-2 text-xs text-muted-foreground">
              Fill in all fields below to reach 100% and improve recommendation accuracy.
            </p>
          )}
        </div>
      )}

      <div className="grid gap-5 sm:grid-cols-2">
        <Field label="Age range" error={errors.age_range?.message}>
          <select
            {...register("age_range")}
            disabled={isPending}
            className={selectClass}
          >
            <option value="">Select age range</option>
            {AGE_RANGES.map((r) => (
              <option key={r} value={r}>{r}</option>
            ))}
          </select>
        </Field>

        <Field label="Education level" error={errors.education_level?.message}>
          <select
            {...register("education_level")}
            disabled={isPending}
            className={selectClass}
          >
            <option value="">Select education level</option>
            {EDUCATION_LEVELS.map((e) => (
              <option key={e} value={e}>{e}</option>
            ))}
          </select>
        </Field>

        <Field
          label="Current field / industry"
          error={errors.current_field?.message}
          hint="e.g. Technology, Healthcare, Finance"
        >
          <input
            type="text"
            placeholder="e.g. Technology"
            disabled={isPending}
            className={inputClass}
            {...register("current_field")}
          />
        </Field>

        <Field
          label="Years of experience"
          error={errors.years_of_experience?.message}
        >
          <input
            type="number"
            min={0}
            max={60}
            placeholder="0"
            disabled={isPending}
            className={inputClass}
            {...register("years_of_experience", { valueAsNumber: true })}
          />
        </Field>

        <Field label="Country" error={errors.country?.message}>
          <input
            type="text"
            placeholder="e.g. India"
            disabled={isPending}
            className={inputClass}
            {...register("country")}
          />
        </Field>

        <Field
          label="Preferred work environment"
          error={errors.desired_work_environment?.message}
        >
          <select
            {...register("desired_work_environment")}
            disabled={isPending}
            className={selectClass}
          >
            <option value="">Select preference</option>
            {WORK_ENVIRONMENTS.map((e) => (
              <option key={e} value={e}>{e}</option>
            ))}
          </select>
        </Field>
      </div>

      <Field
        label="Primary career goal"
        error={errors.primary_goal?.message}
        hint="Describe what you want to achieve in your career (max 500 characters)"
      >
        <textarea
          rows={3}
          placeholder="e.g. Become a senior software engineer at a product company"
          disabled={isPending}
          className={cn(inputClass, "resize-none")}
          {...register("primary_goal")}
        />
      </Field>

      {/* Status messages */}
      {isSuccess && (
        <p className="text-sm text-emerald-600 dark:text-emerald-400">
          ✓ Profile updated successfully
        </p>
      )}
      {isError && (
        <p className="text-sm text-destructive">
          {error instanceof Error ? error.message : "Failed to update profile"}
        </p>
      )}

      <div className="flex justify-end">
        <button
          type="submit"
          disabled={isPending || !isDirty}
          className={cn(
            "inline-flex items-center gap-2 rounded-lg bg-primary px-5 py-2",
            "text-sm font-semibold text-primary-foreground",
            "transition-opacity hover:opacity-90",
            "disabled:cursor-not-allowed disabled:opacity-50",
          )}
        >
          {isPending ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <Save className="h-4 w-4" />
          )}
          {isPending ? "Saving…" : "Save changes"}
        </button>
      </div>
    </form>
  );
}
