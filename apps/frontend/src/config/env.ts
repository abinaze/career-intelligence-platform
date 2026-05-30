/**
 * Typed and validated environment configuration.
 *
 * All environment access goes through this module.
 * Never access process.env directly in application code.
 */

function optionalEnv(key: string, fallback: string): string {
  return process.env[key] ?? fallback;
}

export const env = {
  apiUrl: optionalEnv("NEXT_PUBLIC_API_URL", "http://localhost:8000"),
  appUrl: optionalEnv("NEXT_PUBLIC_APP_URL", "http://localhost:3000"),
  appVersion: optionalEnv("NEXT_PUBLIC_APP_VERSION", "0.1.0"),

  isDevelopment: process.env.NODE_ENV === "development",
  isProduction: process.env.NODE_ENV === "production",
  isTest: process.env.NODE_ENV === "test",

  appName: "Career Intelligence Platform",
} as const;
