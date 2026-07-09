import { useChatStore } from "../store/chat.store";

/**
 * Convenience hook that exposes the full chat interface to components.
 */
export function useChat() {
  const store = useChatStore();
  return {
    messages: store.messages,
    isLoading: store.status === "loading",
    error: store.error,
    sendMessage: store.sendMessage,
    clearChat: store.clearChat,
    clearError: store.clearError,
  };
}
