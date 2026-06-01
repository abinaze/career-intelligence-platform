import { apiClient } from "@/lib/api/client";
import type {
  AuthResponse,
  AuthTokens,
  LoginCredentials,
  RegisterCredentials,
  User,
} from "@/types/auth";

/**
 * Auth API layer.
 *
 * All HTTP calls related to authentication live here.
 * The auth store calls these functions — components never
 * call the API client directly.
 */
export const authApi = {
  /**
   * Login using OAuth2 password flow.
   * FastAPI expects multipart form data for the /token endpoint.
   */
  async login(credentials: LoginCredentials): Promise<AuthResponse> {
    const formData = new FormData();
    formData.append("username", credentials.email);
    formData.append("password", credentials.password);

    const tokenResponse = await apiClient.post<AuthTokens>(
      "/auth/token",
      formData,
      { headers: { "Content-Type": "multipart/form-data" } },
    );

    const userResponse = await apiClient.get<User>("/auth/me");

    return {
      tokens: tokenResponse.data,
      user: userResponse.data,
    };
  },

  /**
   * Register a new account then immediately log in.
   */
  async register(credentials: RegisterCredentials): Promise<AuthResponse> {
    await apiClient.post("/auth/register", credentials);
    return authApi.login({
      email: credentials.email,
      password: credentials.password,
    });
  },

  /**
   * Revoke the refresh token on the server.
   * Best-effort — failure is silently ignored during logout.
   */
  async logout(refreshToken: string): Promise<void> {
    await apiClient.post("/auth/logout", {
      refresh_token: refreshToken,
    });
  },

  /**
   * Fetch the authenticated user's profile.
   */
  async getMe(): Promise<User> {
    const response = await apiClient.get<User>("/auth/me");
    return response.data;
  },

  /**
   * Request a password reset email.
   */
  async requestPasswordReset(email: string): Promise<void> {
    await apiClient.post("/auth/password-reset/request", { email });
  },

  /**
   * Confirm a password reset with token and new password.
   */
  async confirmPasswordReset(
    token: string,
    newPassword: string,
  ): Promise<void> {
    await apiClient.post("/auth/password-reset/confirm", {
      token,
      new_password: newPassword,
    });
  },
};
