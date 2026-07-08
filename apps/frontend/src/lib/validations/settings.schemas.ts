import { z } from "zod";

export const profileSchema = z.object({
  age_range: z.string().optional(),
  education_level: z.string().optional(),
  current_field: z
    .string()
    .max(200, "Field must be less than 200 characters")
    .optional(),
  years_of_experience: z
    .number({ invalid_type_error: "Must be a number" })
    .int()
    .min(0, "Must be 0 or more")
    .max(60, "Must be 60 or less")
    .optional(),
  country: z
    .string()
    .max(100, "Country must be less than 100 characters")
    .optional(),
  primary_goal: z
    .string()
    .max(500, "Goal must be less than 500 characters")
    .optional(),
  desired_work_environment: z.string().optional(),
});

export const accountSchema = z
  .object({
    full_name: z
      .string()
      .min(2, "Full name must be at least 2 characters")
      .max(255, "Full name must be less than 255 characters")
      .regex(/^[a-zA-Z\s'-]+$/, "Full name contains invalid characters"),
    email: z
      .string()
      .min(1, "Email is required")
      .email("Please enter a valid email address"),
  });

export const changePasswordSchema = z
  .object({
    current_password: z.string().min(1, "Current password is required"),
    new_password: z
      .string()
      .min(8, "Password must be at least 8 characters")
      .regex(/[A-Z]/, "Must contain an uppercase letter")
      .regex(/[a-z]/, "Must contain a lowercase letter")
      .regex(/[0-9]/, "Must contain a number"),
    confirm_password: z.string().min(1, "Please confirm your password"),
  })
  .refine((d) => d.new_password === d.confirm_password, {
    message: "Passwords do not match",
    path: ["confirm_password"],
  });

export type ProfileSchema = z.infer<typeof profileSchema>;
export type AccountSchema = z.infer<typeof accountSchema>;
export type ChangePasswordSchema = z.infer<typeof changePasswordSchema>;
