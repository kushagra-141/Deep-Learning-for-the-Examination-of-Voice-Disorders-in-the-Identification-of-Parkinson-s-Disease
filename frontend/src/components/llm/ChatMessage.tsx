import { motion } from "framer-motion";
import { Bot, User } from "lucide-react";
import { ToolBadge } from "./ToolBadge";
import type { UiMessage } from "../../lib/schemas/chat";

interface ChatMessageProps {
  message: UiMessage;
}

function renderMarkdown(text: string): React.ReactNode[] {
  // Basic bold/italic support; keeps the component dep-free.
  const lines = text.split("\n");
  return lines.map((line, i) => {
    const parts = line.split(/\*\*(.*?)\*\*/g);
    return (
      <p key={i} className={i < lines.length - 1 ? "mb-2" : ""}>
        {parts.map((part, j) =>
          j % 2 === 1 ? (
            <strong key={j} className="font-semibold text-foreground">
              {part}
            </strong>
          ) : (
            part
          ),
        )}
      </p>
    );
  });
}

export function ChatMessage({ message }: ChatMessageProps) {
  const isUser = message.role === "user";

  return (
    <motion.div
      initial={{ opacity: 0, y: 6 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.2 }}
      className={`flex gap-2.5 ${isUser ? "flex-row-reverse" : "flex-row"}`}
    >
      <div
        className={`shrink-0 h-7 w-7 rounded-full flex items-center justify-center text-xs font-bold mt-0.5 ${
          isUser ? "bg-primary text-primary-foreground" : "bg-muted text-muted-foreground"
        }`}
        aria-hidden="true"
      >
        {isUser ? <User className="h-3.5 w-3.5" /> : <Bot className="h-3.5 w-3.5" />}
      </div>

      <div className={`flex-1 min-w-0 space-y-1.5 ${isUser ? "items-end" : "items-start"} flex flex-col`}>
        {/* Tool badges above the assistant bubble */}
        {!isUser && message.tools && message.tools.length > 0 && (
          <div className="flex flex-wrap gap-1.5">
            {message.tools.map((t, i) => (
              <ToolBadge key={`${t.name}-${i}`} tool={t} />
            ))}
          </div>
        )}

        {/* Message bubble */}
        {(message.content || message.streaming) && (
          <div
            className={`rounded-2xl px-3.5 py-2.5 text-sm leading-relaxed max-w-[92%] ${
              isUser
                ? "bg-primary text-primary-foreground rounded-tr-sm"
                : "bg-muted text-foreground rounded-tl-sm"
            }`}
          >
            {message.content ? (
              <div className="prose-sm">{renderMarkdown(message.content)}</div>
            ) : (
              <span className="inline-flex items-center gap-1 text-muted-foreground">
                <span className="animate-bounce" style={{ animationDelay: "0ms" }}>·</span>
                <span className="animate-bounce" style={{ animationDelay: "150ms" }}>·</span>
                <span className="animate-bounce" style={{ animationDelay: "300ms" }}>·</span>
              </span>
            )}
            {message.streaming && message.content && (
              <span
                className="inline-block w-0.5 h-3.5 bg-current ml-0.5 align-middle animate-pulse"
                aria-hidden="true"
              />
            )}
          </div>
        )}

        {/* Disclaimer badge on assistant messages */}
        {!isUser && !message.streaming && message.content && (
          <span className="text-[9px] text-muted-foreground">Not medical advice</span>
        )}
      </div>
    </motion.div>
  );
}
