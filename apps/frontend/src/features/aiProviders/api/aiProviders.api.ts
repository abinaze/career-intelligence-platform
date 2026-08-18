import { apiClient } from "@/lib/api/client";
import type { TestConnectionResponse } from "../types";

/**
 * Client for the backend's chat key-validation endpoint
 * (`POST /chat/test-connection`). The backend makes exactly one
 * minimal Anthropic API call with the supplied key and never persists
 * it — see src/services/chat/llm_provider.py's verify_anthropic_key.
 */
export const aiProvidersApi = {
  async testAnthropicKey(apiKey: string): Promise<TestConnectionResponse> {
    const response = await apiClient.post<TestConnectionResponse>("/chat/test-connection", {
      api_key: apiKey,
    });
    return response.data;
  },
};
