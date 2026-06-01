import { create } from "zustand";
import { persist, createJSONStorage } from "zustand/middleware";
import { immer } from "zustand/middleware/immer";
import type {
  User,
  AuthTokens,
  LoginCredentials,
  RegisterCredentials,
} from "@/types/auth";
import { authApi } from "../api/auth.api";

interface AuthStore {
  user: User | null;
  tokens: AuthTokens | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;

  login: (credentials: LoginCredentials) => Promise<void>;
  register: (credentials: RegisterCredentials) => Promise<void>;
  logout: () => Promise<void>;
  refreshUser: () => Promise<void>;
  clearError: () => void;
  setTokens: (tokens: AuthTokens) => void;
}

/**
 * Global auth store.
 *
 * Persists user and token data to localStorage so sessions
 * survive page refresh. Sensitive data (passwords) never
 * enters this store.
 */
export const useAuthStore = create<AuthStore>()(
  persist(
    immer((set, get) => ({
      user: null,
      tokens: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,

      login: async (credentials) => {
        set((state) => {
          state.isLoading = true;
          state.error = null;
        });

        try {
          const { tokens, user } = await authApi.login(credentials);

          if (typeof window !== "undefined") {
            localStorage.setItem("access_token", tokens.access_token);
            localStorage.setItem("refresh_token", tokens.refresh_token);
          }

          set((state) => {
            state.user = user;
            state.tokens = tokens;
            state.isAuthenticated = true;
            state.isLoading = false;
          });
        } catch (error) {
          const message =
            error instanceof Error
              ? error.message
              : "Authentication failed";
          set((state) => {
            state.error = message;
            state.isLoading = false;
          });
          throw error;
        }
      },

      register: async (credentials) => {
        set((state) => {
          state.isLoading = true;
          state.error = null;
        });

        try {
          const { tokens, user } = await authApi.register(credentials);

          if (typeof window !== "undefined") {
            localStorage.setItem("access_token", tokens.access_token);
            localStorage.setItem("refresh_token", tokens.refresh_token);
          }

          set((state) => {
            state.user = user;
            state.tokens = tokens;
            state.isAuthenticated = true;
            state.isLoading = false;
          });
        } catch (error) {
          const message =
            error instanceof Error
              ? error.message
              : "Registration failed";
          set((state) => {
            state.error = message;
            state.isLoading = false;
          });
          throw error;
        }
      },

      logout: async () => {
        set((state) => {
          state.isLoading = true;
        });

        try {
          const refreshToken = get().tokens?.refresh_token;
          if (refreshToken) {
            await authApi.logout(refreshToken).catch(() => {
              // Best-effort server logout — ignore failures
            });
          }
        } finally {
          if (typeof window !== "undefined") {
            localStorage.removeItem("access_token");
            localStorage.removeItem("refresh_token");
          }

          set((state) => {
            state.user = null;
            state.tokens = null;
            state.isAuthenticated = false;
            state.isLoading = false;
          });
        }
      },

      refreshUser: async () => {
        try {
          const user = await authApi.getMe();
          set((state) => {
            state.user = user;
          });
        } catch {
          await get().logout();
        }
      },

      clearError: () => {
        set((state) => {
          state.error = null;
        });
      },

      setTokens: (tokens) => {
        if (typeof window !== "undefined") {
          localStorage.setItem("access_token", tokens.access_token);
          localStorage.setItem("refresh_token", tokens.refresh_token);
        }
        set((state) => {
          state.tokens = tokens;
          state.isAuthenticated = true;
        });
      },
    })),
    {
      name: "auth-store",
      storage: createJSONStorage(() => localStorage),
      partialize: (state) => ({
        user: state.user,
        tokens: state.tokens,
        isAuthenticated: state.isAuthenticated,
      }),
    },
  ),
);
