"use client";

import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { Eye, EyeOff, Loader2, Lock } from "lucide-react";
import { cn } from "@/lib/utils";
import {
  changePasswordSchema,
  type ChangePasswordSchema,
} from "@/lib/validations/settings.schemas";

const inputClass = cn(
  "w-full rounded-lg border border-input bg-background py-2.5 pl-10 pr-10 text-sm",
  "placeholder:text-muted-foreground",
  "focus:outline-none focus:ring-2 focus:ring-ring",
  "disabled:cursor-not-allowed disabled:opacity-50",
);

function PasswordField({
  id,
  label,
  placeholder,
  disabled,
  error,
  registration,
}: {
  id: string;
  label: string;
  placeholder: string;
  disabled: boolean;
  error?: string;
  registration: ReturnType<ReturnType<typeof useForm>["register"]>;
}) {
  const [show, setShow] = useState(false);
  return (
    <div className="space-y-1.5">
      <label htmlFor={id} className="text-sm font-medium text-foreground">
        {label}
      </label>
      <div className="relative">
        <Lock className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
        <input
          id={id}
          type={show ? "text" : "password"}
          placeholder={placeholder}
          disabled={disabled}
          className={cn(inputClass, error && "border-destructive")}
          {...registration}
        />
        <button
          type="button"
          onClick={() => setShow((v) => !v)}
          className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
          tabIndex={-1}
        >
          {show ? (
            <EyeOff className="h-4 w-4" />
          ) : (
            <Eye className="h-4 w-4" />
          )}
        </button>
      </div>
      {error && <p className="text-xs text-destructive">{error}</p>}
    </div>
  );
}

export function ChangePasswordForm() {
  const [success, setSuccess] = useState(false);
  const [serverError, setServerError] = useState<string | null>(null);
  const [isPending, setIsPending] = useState(false);

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<ChangePasswordSchema>({
    resolver: zodResolver(changePasswordSchema),
    defaultValues: {
      current_password: "",
      new_password: "",
      confirm_password: "",
    },
  });

  async function onSubmit(_values: ChangePasswordSchema) {
    setIsPending(true);
    setServerError(null);
    setSuccess(false);
    try {
      // TODO: wire to POST /auth/change-password when backend endpoint is available
      await new Promise((r) => setTimeout(r, 600)); // simulate pending
      setSuccess(true);
      reset();
    } catch (err) {
      setServerError(
        err instanceof Error ? err.message : "Failed to change password",
      );
    } finally {
      setIsPending(false);
    }
  }

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-5">
      <PasswordField
        id="current_password"
        label="Current password"
        placeholder="••••••••"
        disabled={isPending}
        error={errors.current_password?.message}
        registration={register("current_password")}
      />
      <PasswordField
        id="new_password"
        label="New password"
        placeholder="Min 8 chars, uppercase, lowercase, number"
        disabled={isPending}
        error={errors.new_password?.message}
        registration={register("new_password")}
      />
      <PasswordField
        id="confirm_password"
        label="Confirm new password"
        placeholder="••••••••"
        disabled={isPending}
        error={errors.confirm_password?.message}
        registration={register("confirm_password")}
      />

      {success && (
        <p className="text-sm text-emerald-600 dark:text-emerald-400">
          ✓ Password changed successfully
        </p>
      )}
      {serverError && (
        <p className="text-sm text-destructive">{serverError}</p>
      )}

      <div className="flex justify-end">
        <button
          type="submit"
          disabled={isPending}
          className={cn(
            "inline-flex items-center gap-2 rounded-lg bg-primary px-5 py-2",
            "text-sm font-semibold text-primary-foreground",
            "transition-opacity hover:opacity-90",
            "disabled:cursor-not-allowed disabled:opacity-50",
          )}
        >
          {isPending && <Loader2 className="h-4 w-4 animate-spin" />}
          {isPending ? "Updating…" : "Update password"}
        </button>
      </div>
    </form>
  );
}
