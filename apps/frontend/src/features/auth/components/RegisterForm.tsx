"use client";

import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { motion } from "framer-motion";
import { Loader2, Mail, Lock, User } from "lucide-react";
import { cn } from "@/lib/utils/cn";
import {
  registerSchema,
  type RegisterSchema,
} from "@/lib/validations/auth.schemas";
import { useAuth } from "../hooks/useAuth";

/**
 * Registration form component.
 *
 * Collects full name, email, password, and confirmation.
 * Validates password strength requirements inline.
 */
export function RegisterForm() {
  const { register: registerUser, isLoading, error, clearError } = useAuth();

  const {
    register,
    handleSubmit,
    watch,
    formState: { errors },
  } = useForm<RegisterSchema>({
    resolver: zodResolver(registerSchema),
    defaultValues: {
      full_name: "",
      email: "",
      password: "",
      confirm_password: "",
    },
  });

  const password = watch("password");
  const passwordStrength = getPasswordStrength(password);

  async function onSubmit(values: RegisterSchema) {
    clearError();
    try {
      await registerUser({
        email: values.email,
        password: values.password,
        full_name: values.full_name,
      });
    } catch {
      // Error is already set in the store
    }
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className="w-full max-w-md"
    >
      <div className="rounded-xl border border-border/50 bg-card p-8 shadow-xl">
        <div className="mb-6 text-center">
          <h1 className="text-2xl font-bold tracking-tight text-foreground">
            Create your account
          </h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Start your AI-powered career intelligence journey
          </p>
        </div>

        <form
          onSubmit={handleSubmit(onSubmit)}
          noValidate
          className="space-y-4"
        >
          {error && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: "auto" }}
              className="rounded-lg bg-destructive/10 px-4 py-3 text-sm text-destructive"
              role="alert"
            >
              {error}
            </motion.div>
          )}

          <div className="space-y-1.5">
            <label
              htmlFor="full_name"
              className="text-sm font-medium text-foreground"
            >
              Full name
            </label>
            <div className="relative">
              <User className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
              <input
                id="full_name"
                type="text"
                placeholder="Jane Doe"
                autoComplete="name"
                disabled={isLoading}
                className={cn(
                  "w-full rounded-lg border bg-background px-10 py-2.5 text-sm",
                  "placeholder:text-muted-foreground",
                  "focus:outline-none focus:ring-2 focus:ring-ring",
                  "disabled:cursor-not-allowed disabled:opacity-50",
                  errors.full_name ? "border-destructive" : "border-input",
                )}
                {...register("full_name")}
              />
            </div>
            {errors.full_name && (
              <p className="text-xs text-destructive">
                {errors.full_name.message}
              </p>
            )}
          </div>

          <div className="space-y-1.5">
            <label
              htmlFor="email"
              className="text-sm font-medium text-foreground"
            >
              Email address
            </label>
            <div className="relative">
              <Mail className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
              <input
                id="email"
                type="email"
                placeholder="you@example.com"
                autoComplete="email"
                disabled={isLoading}
                className={cn(
                  "w-full rounded-lg border bg-background px-10 py-2.5 text-sm",
                  "placeholder:text-muted-foreground",
                  "focus:outline-none focus:ring-2 focus:ring-ring",
                  "disabled:cursor-not-allowed disabled:opacity-50",
                  errors.email ? "border-destructive" : "border-input",
                )}
                {...register("email")}
              />
            </div>
            {errors.email && (
              <p className="text-xs text-destructive">
                {errors.email.message}
              </p>
            )}
          </div>

          <div className="space-y-1.5">
            <label
              htmlFor="password"
              className="text-sm font-medium text-foreground"
            >
              Password
            </label>
            <div className="relative">
              <Lock className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
              <input
                id="password"
                type="password"
                placeholder="••••••••"
                autoComplete="new-password"
                disabled={isLoading}
                className={cn(
                  "w-full rounded-lg border bg-background px-10 py-2.5 text-sm",
                  "placeholder:text-muted-foreground",
                  "focus:outline-none focus:ring-2 focus:ring-ring",
                  "disabled:cursor-not-allowed disabled:opacity-50",
                  errors.password ? "border-destructive" : "border-input",
                )}
                {...register("password")}
              />
            </div>
            {password && (
              <div className="space-y-1">
                <div className="flex gap-1">
                  {[1, 2, 3, 4].map((level) => (
                    <div
                      key={level}
                      className={cn(
                        "h-1 flex-1 rounded-full transition-colors",
                        level <= passwordStrength.score
                          ? passwordStrength.color
                          : "bg-muted",
                      )}
                    />
                  ))}
                </div>
                <p className="text-xs text-muted-foreground">
                  {passwordStrength.label}
                </p>
              </div>
            )}
            {errors.password && (
              <p className="text-xs text-destructive">
                {errors.password.message}
              </p>
            )}
          </div>

          <div className="space-y-1.5">
            <label
              htmlFor="confirm_password"
              className="text-sm font-medium text-foreground"
            >
              Confirm password
            </label>
            <div className="relative">
              <Lock className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
              <input
                id="confirm_password"
                type="password"
                placeholder="••••••••"
                autoComplete="new-password"
                disabled={isLoading}
                className={cn(
                  "w-full rounded-lg border bg-background px-10 py-2.5 text-sm",
                  "placeholder:text-muted-foreground",
                  "focus:outline-none focus:ring-2 focus:ring-ring",
                  "disabled:cursor-not-allowed disabled:opacity-50",
                  errors.confirm_password
                    ? "border-destructive"
                    : "border-input",
                )}
                {...register("confirm_password")}
              />
            </div>
            {errors.confirm_password && (
              <p className="text-xs text-destructive">
                {errors.confirm_password.message}
              </p>
            )}
          </div>

          <button
            type="submit"
            disabled={isLoading}
            className={cn(
              "w-full rounded-lg bg-primary px-4 py-2.5 text-sm font-medium",
              "text-primary-foreground transition-opacity",
              "hover:opacity-90 focus:outline-none focus:ring-2 focus:ring-ring",
              "disabled:cursor-not-allowed disabled:opacity-50",
              "flex items-center justify-center gap-2",
            )}
          >
            {isLoading ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" />
                Creating account...
              </>
            ) : (
              "Create account"
            )}
          </button>
        </form>

        <div className="mt-6 text-center">
          <p className="text-sm text-muted-foreground">
            Already have an account?{" "}
            <a
              href="/login"
              className="font-medium text-primary underline-offset-4 hover:underline"
            >
              Sign in
            </a>
          </p>
        </div>
      </div>
    </motion.div>
  );
}

interface PasswordStrength {
  score: number;
  label: string;
  color: string;
}

function getPasswordStrength(password: string): PasswordStrength {
  if (!password) {
    return { score: 0, label: "", color: "bg-muted" };
  }

  let score = 0;
  if (password.length >= 8) score++;
  if (/[A-Z]/.test(password)) score++;
  if (/[0-9]/.test(password)) score++;
  if (/[^A-Za-z0-9]/.test(password)) score++;

  const levels: PasswordStrength[] = [
    { score: 1, label: "Weak", color: "bg-red-500" },
    { score: 2, label: "Fair", color: "bg-orange-500" },
    { score: 3, label: "Good", color: "bg-yellow-500" },
    { score: 4, label: "Strong", color: "bg-emerald-500" },
  ];

  return (
    levels[score - 1] ?? {
      score: 1,
      label: "Weak",
      color: "bg-red-500",
    }
  );
}
