import { useRef, type KeyboardEvent } from "react";
import { Send, Square } from "lucide-react";
import { Button } from "../ui/button";

interface ChatComposerProps {
  onSend: (text: string) => void;
  onStop: () => void;
  isStreaming: boolean;
  disabled?: boolean;
}

export function ChatComposer({ onSend, onStop, isStreaming, disabled }: ChatComposerProps) {
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const submit = () => {
    const value = textareaRef.current?.value.trim() ?? "";
    if (!value || isStreaming) return;
    onSend(value);
    if (textareaRef.current) textareaRef.current.value = "";
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      submit();
    }
  };

  const handleInput = () => {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = `${Math.min(el.scrollHeight, 120)}px`;
  };

  return (
    <div className="flex gap-2 items-end">
      <textarea
        ref={textareaRef}
        rows={1}
        onKeyDown={handleKeyDown}
        onInput={handleInput}
        disabled={disabled || isStreaming}
        placeholder="Ask about your result… (Enter to send, Shift+Enter for newline)"
        aria-label="Chat message"
        className="flex-1 resize-none rounded-lg border border-input bg-background px-3 py-2 text-sm leading-snug min-h-[38px] max-h-[120px] focus:outline-none focus:ring-2 focus:ring-ring disabled:opacity-60 placeholder:text-muted-foreground"
      />
      {isStreaming ? (
        <Button
          type="button"
          size="icon"
          variant="outline"
          onClick={onStop}
          aria-label="Stop generation"
          className="shrink-0"
        >
          <Square className="h-4 w-4" />
        </Button>
      ) : (
        <Button
          type="button"
          size="icon"
          onClick={submit}
          disabled={disabled}
          aria-label="Send message"
          className="shrink-0"
        >
          <Send className="h-4 w-4" />
        </Button>
      )}
    </div>
  );
}
