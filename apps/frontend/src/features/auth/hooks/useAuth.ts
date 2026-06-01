import { useRouter } from "next/navigation";
import { useAuthStore } from "../store/auth.store";
import type { LoginCredentials, RegisterCredentials } from "@/types/auth";

/**
 * Primary auth hook for components.
 *
 * Wraps the auth store and adds navigation side effects.
 * Components should use this hook instead of the store directly.
 */
export function useAuth() {
  const router = useRouter();
  const store = useAuthStore();

  async function login(credentials: LoginCredentials): Promise<void> {
    await store.login(credentials);
    router.push("/dashboard");
  }

  async function register(
    credentials: RegisterCredentials,
  ): Promise<void> {
    await store.register(credentials);
    router.push("/dashboard");
  }

  async function logout(): Promise<void> {
    await store.logout();
    router.push("/login");
  }

  return {
    user: store.user,
    isAuthenticated: store.isAuthenticated,
    isLoading: store.isLoading,
    error: store.error,
    login,
    register,
    logout,
    clearError: store.clearError,
    refreshUser: store.refreshUser,
  };
}
