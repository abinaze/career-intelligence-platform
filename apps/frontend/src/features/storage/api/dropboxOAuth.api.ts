import { apiClient } from "@/lib/api/client";

/**
 * Client for the backend's Dropbox OAuth broker (`/storage/dropbox/*`,
 * see docs/api/reference.md and docs/architecture/byos.md). Same shape
 * as googleDriveOAuth.api.ts, including disconnect() — unlike OneDrive,
 * Dropbox has a real token-revoke endpoint.
 */

export interface DropboxTokenResponse {
  access_token: string;
  refresh_token: string | null;
  token_type: string;
  expires_at: string;
  scope: string;
}

interface DropboxConnectResponse {
  authorize_url: string;
}

interface DropboxDisconnectResponse {
  revoked: boolean;
}

export const dropboxOAuthApi = {
  /** Starts a connect flow; returns the Dropbox authorization URL for a full-page redirect. */
  async getAuthorizeUrl(): Promise<string> {
    const response = await apiClient.get<DropboxConnectResponse>("/storage/dropbox/connect");
    return response.data.authorize_url;
  },

  /** Claims the exchange code staged by the backend's /callback redirect. Single-use. */
  async claimExchange(exchangeCode: string): Promise<DropboxTokenResponse> {
    const response = await apiClient.post<DropboxTokenResponse>("/storage/dropbox/exchange", {
      exchange_code: exchangeCode,
    });
    return response.data;
  },

  /** Exchanges a refresh token for a new access token. Dropbox doesn't rotate the refresh token. */
  async refresh(refreshToken: string): Promise<DropboxTokenResponse> {
    const response = await apiClient.post<DropboxTokenResponse>("/storage/dropbox/refresh", {
      refresh_token: refreshToken,
    });
    return response.data;
  },

  /**
   * Revokes a token at Dropbox. Pass an **access token**, not a refresh
   * token — Dropbox's revoke endpoint authenticates as the token itself.
   */
  async disconnect(accessToken: string): Promise<boolean> {
    const response = await apiClient.post<DropboxDisconnectResponse>(
      "/storage/dropbox/disconnect",
      {
        token: accessToken,
      },
    );
    return response.data.revoked;
  },
};
