import { apiClient } from "@/lib/api/client";

/**
 * Client for the backend's OneDrive OAuth broker (`/storage/onedrive/*`,
 * see docs/api/reference.md and docs/architecture/byos.md). Same shape
 * as googleDriveOAuth.api.ts, with one difference: there's no
 * `disconnect()` — Microsoft has no simple per-token revoke API for this
 * flow, so disconnecting OneDrive is handled entirely client-side (see
 * OneDriveConnect.tsx, which just clears stored tokens directly).
 */

export interface OneDriveTokenResponse {
  access_token: string;
  refresh_token: string | null;
  token_type: string;
  expires_at: string;
  scope: string;
}

interface OneDriveConnectResponse {
  authorize_url: string;
}

export const oneDriveOAuthApi = {
  /**
   * Starts a connect flow and returns the Microsoft authorization URL to
   * send the browser to (full-page redirect, same as Google Drive).
   */
  async getAuthorizeUrl(): Promise<string> {
    const response = await apiClient.get<OneDriveConnectResponse>("/storage/onedrive/connect");
    return response.data.authorize_url;
  },

  /** Claims the exchange code staged by the backend's /callback redirect. Single-use. */
  async claimExchange(exchangeCode: string): Promise<OneDriveTokenResponse> {
    const response = await apiClient.post<OneDriveTokenResponse>("/storage/onedrive/exchange", {
      exchange_code: exchangeCode,
    });
    return response.data;
  },

  /** Exchanges a refresh token for a new access token. Microsoft always rotates the refresh token on use. */
  async refresh(refreshToken: string): Promise<OneDriveTokenResponse> {
    const response = await apiClient.post<OneDriveTokenResponse>("/storage/onedrive/refresh", {
      refresh_token: refreshToken,
    });
    return response.data;
  },
};
