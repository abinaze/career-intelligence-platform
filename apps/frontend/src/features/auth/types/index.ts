/**
 * Auth feature local types.
 * Extends the global auth types with UI-specific state shapes.
 */

export interface LoginFormValues {
  email: string;
  password: string;
}

export interface RegisterFormValues {
  full_name: string;
  email: string;
  password: string;
  confirm_password: string;
}

export interface ForgotPasswordFormValues {
  email: string;
}

export interface ResetPasswordFormValues {
  password: string;
  confirm_password: string;
}

export interface AuthStoreState {
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
}
