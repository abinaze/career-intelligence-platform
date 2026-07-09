import { ChatWindow } from "@/features/chat/components/ChatWindow";

export default function ChatPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Chat</h1>
        <p className="text-muted-foreground">
          Get personalised career advice from your AI counsellor.
        </p>
      </div>
      <ChatWindow />
    </div>
  );
}
