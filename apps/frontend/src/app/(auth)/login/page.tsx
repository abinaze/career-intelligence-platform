import type { Metadata } from "next";
import { LoginForm } from "@/features/auth/components/LoginForm";

export const metadata: Metadata = {
  title: "Sign In",
  description: "Sign in to your Career Intelligence Platform account.",
};

/**
 * Login page.
 * Route: /login
 */
export default function LoginPage() {
  return <LoginForm />;
}
