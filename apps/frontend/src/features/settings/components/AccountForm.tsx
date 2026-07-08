"use client";

import { useEffect } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { Loader2, Save, ShieldCheck } from "lucide-react";
import { cn } from "@/lib/utils";
import {
  accountSchema,
  type AccountSchema,
} from "@/lib/validations/settings.schemas";
import { useAuth } from "@/features/auth/hooks/useAuth";

const inputClass = cn(
  "w-full rounded-lg border border-input bg-background px-3 py-2.5 text-sm",
  "placeholder:text-muted-foreground",
  "focus:outline-none focus:ring-2 focus:ring-ring",
  "disabled:cursor-not-allowed disabled:opacity-50",
);

export function AccountForm() {
  const { user } = useAuth();

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isDirty },
  } = useForm<AccountSchema>({
    resolver: zodResolver(accountSchema),
    defaultValues: { full_name: "", email: "" },
  });

  useEffect(() => {
    if (user) {
      reset({ full_name: user.full_name, email: user.email });
    }
  }, [user, reset]);

  // Account updates would need a backend endpoint — for now show read-only
  // with a note. The form is wired and ready to call an updateAccount mutation.
  function onSubmit(_values: AccountSchema) {
    // TODO: wire to PATCH /auth/me when backend endpoint is available
  }

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-5">
      <div className="grid gap-5 sm:grid-cols-2">
        <div className="space-y-1.5">
          <label className="text-sm font-medium text-foreground">
            Full name
          </label>
          <input
            type="text"
            placeholder="Jane Doe"
            autoComplete="name"
            disabled
            className={cn(inputClass, "opacity-60")}
            {...register("full_name")}
          />
          {errors.full_name && (
            <p className="text-xs text-destructive">
              {errors.full_name.message}
            </p>
          )}
        </div>

        <div className="space-y-1.5">
          <label className="text-sm font-medium text-foreground">
            Email address
          </label>
          <input
            type="email"
            placeholder="you@example.com"
            autoComplete="email"
            disabled
            className={cn(inputClass, "opacity-60")}
            {...register("email")}
          />
          {errors.email && (
            <p className="text-xs text-destructive">{errors.email.message}</p>
          )}
        </div>
      </div>

      {/* Verified badge */}
      {user?.is_verified && (
        <div className="flex items-center gap-2 text-sm text-emerald-600 dark:text-emerald-400">
          <ShieldCheck className="h-4 w-4" />
          Email address verified
        </div>
      )}

      <p className="text-xs text-muted-foreground">
        Account name and email updates are not yet available. Contact support if
        you need to change these details.
      </p>

      <div className="flex justify-end">
        <button
          type="submit"
          disabled={!isDirty}
          className={cn(
            "inline-flex items-center gap-2 rounded-lg bg-primary px-5 py-2",
            "text-sm font-semibold text-primary-foreground",
            "transition-opacity hover:opacity-90",
            "disabled:cursor-not-allowed disabled:opacity-50",
          )}
        >
          <Save className="h-4 w-4" />
          Save changes
        </button>
      </div>
    </form>
  );
}
