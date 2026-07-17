import { apiClient } from "@/lib/api/client";

/**
 * Client for the backend's Google Drive OAuth broker
 * (`/storage/google-drive/*`, see docs/api/reference.md and
 * docs/architecture/byos.md). The backend never persists the tokens
 * these calls return — GoogleDriveAdapter is responsible for storing
 * them client-side (see googleDriveTokens.ts) and calling the Drive
 * REST API directly from then on (see googleDriveClient.ts).
 */

export interface GoogleDriveTokenResponse {
  access_token: string;
  refresh_token: string | null;
  token_type: string;
  expires_at: string;
  scope: string;
}

interface GoogleDriveConnectResponse {
  authorize_url: string;
}

interface GoogleDriveDisconnectResponse {
  revoked: boolean;
}

export const googleDriveOAuthApi = {
  /**
   * Starts a connect flow and returns the Google authorization URL to
   * send the browser to. The caller is expected to do a full-page
   * redirect (`window.location.href = authorize_url`) — Google's own
   * page can't be embedded in an iframe/popup reliably enough to build
   * a popup flow around.
   */
  async getAuthorizeUrl(): Promise<string> {
    const response = await apiClient.get<GoogleDriveConnectResponse>(
      "/storage/google-drive/connect",
    );
    return response.data.authorize_url;
  },

  /**
   * Claims the exchange code staged by the backend's /callback redirect.
   * Single-use — calling this twice with the same code will fail the
   * second time.
   */
  async claimExchange(exchangeCode: string): Promise<GoogleDriveTokenResponse> {
    const response = await apiClient.post<GoogleDriveTokenResponse>(
      "/storage/google-drive/exchange",
      { exchange_code: exchangeCode },
    );
    return response.data;
  },

  /** Exchanges a refresh token for a new access token. */
  async refresh(refreshToken: string): Promise<GoogleDriveTokenResponse> {
    const response = await apiClient.post<GoogleDriveTokenResponse>(
      "/storage/google-drive/refresh",
      { refresh_token: refreshToken },
    );
    return response.data;
  },

  /**
   * Revokes a token at Google. Best-effort from the caller's
   * perspective — the frontend clears its local copy regardless of
   * whether this succeeds (see GoogleDriveConnect.tsx).
   */
  async disconnect(token: string): Promise<boolean> {
    const response = await apiClient.post<GoogleDriveDisconnectResponse>(
      "/storage/google-drive/disconnect",
      { token },
    );
    return response.data.revoked;
  },
};
