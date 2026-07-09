import { apiClient } from "@/lib/api/client";
import type { ChatRequest, ChatResponse } from "../types";

export const chatApi = {
  async sendMessage(payload: ChatRequest): Promise<ChatResponse> {
    const response = await apiClient.post<ChatResponse>(
      "/chat/message",
      payload,
    );
    return response.data;
  },
};
