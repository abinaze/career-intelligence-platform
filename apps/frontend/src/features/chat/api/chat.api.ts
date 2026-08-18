import { apiClient } from "@/lib/api/client";
import { getAnthropicByoKey } from "@/features/aiProviders/lib/anthropicKeyStorage";
import type { ChatRequest, ChatResponse } from "../types";

export const chatApi = {
  async sendMessage(payload: ChatRequest): Promise<ChatResponse> {
    // If the user has connected their own Anthropic key, attach it so
    // the backend uses that instead of the platform's — see
    // src/services/chat/llm_provider.py's resolve_llm_provider, which
    // always prefers a supplied key when present. The key is read from
    // IndexedDB fresh on every call rather than cached in this module,
    // since it can change (connected/removed) between messages.
    const byoKey = await getAnthropicByoKey();
    const response = await apiClient.post<ChatResponse>("/chat/message", payload, {
      headers: byoKey ? { "X-User-Anthropic-Key": byoKey } : {},
    });
    return response.data;
  },
};
