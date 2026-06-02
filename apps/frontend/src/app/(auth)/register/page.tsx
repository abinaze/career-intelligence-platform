import type { Metadata } from "next";
import { RegisterForm } from "@/features/auth/components/RegisterForm";

export const metadata: Metadata = {
  title: "Create Account",
  description:
    "Create your free Career Intelligence Platform account and start your AI-powered career journey.",
};

/**
 * Register page.
 * Route: /register
 */
export default function RegisterPage() {
  return <RegisterForm />;
}
