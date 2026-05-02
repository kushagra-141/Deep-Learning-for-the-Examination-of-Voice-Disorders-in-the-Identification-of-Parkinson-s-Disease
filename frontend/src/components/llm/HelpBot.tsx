import { useEffect, useRef, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { Bot, HelpCircle, Loader2, RotateCcw, Send, X } from "lucide-react";
import { useLocation } from "react-router-dom";
import { Button } from "../ui/button";
import { useHelpBot } from "../../hooks/useHelpBot";

const SUGGESTED = [
  "How do I record audio?",
  "What are these features?",
  "Is this a diagnosis?",
];

const ADMIN_PATTERN = /^\/admin(\/|$)/;

export function HelpBot() {
  const [open, setOpen] = useState(false);
  const [input, setInput] = useState("");
  const { messages, status, ask, reset } = useHelpBot();
  const location = useLocation();
  const bottomRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Hide on admin pages.
  if (ADMIN_PATTERN.test(location.pathname)) return null;

  const isLoading = status === "loading";

  const submit = () => {
    const text = input.trim();
    if (!text || isLoading) return;
    void ask(text);
    setInput("");
  };

  const handleKey = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter") {
      e.preventDefault();
      submit();
    }
    if (e.key === "Escape") setOpen(false);
  };

  // Auto-scroll to latest message.
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // Focus input when popover opens.
  useEffect(() => {
    if (open) setTimeout(() => inputRef.current?.focus(), 50);
  }, [open]);

  return (
    <div className="fixed bottom-5 right-5 z-50 flex flex-col items-end gap-2">
      <AnimatePresence>
        {open && (
          <motion.div
            key="popover"
            initial={{ opacity: 0, y: 12, scale: 0.97 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 12, scale: 0.97 }}
            transition={{ duration: 0.2 }}
            className="w-80 max-h-[480px] flex flex-col rounded-2xl border bg-background shadow-2xl overflow-hidden"
            role="dialog"
            aria-label="Help bot"
          >
            {/* Header */}
            <div className="flex items-center justify-between px-4 py-3 border-b bg-muted/30 shrink-0">
              <div className="flex items-center gap-2">
                <Bot className="h-4 w-4 text-primary" />
                <span className="text-sm font-semibold">Help</span>
              </div>
              <div className="flex items-center gap-1">
                {messages.length > 0 && (
                  <button
                    type="button"
                    onClick={reset}
                    className="p-1 rounded hover:bg-accent transition-colors"
                    aria-label="Clear"
                  >
                    <RotateCcw className="h-3.5 w-3.5 text-muted-foreground" />
                  </button>
                )}
                <button
                  type="button"
                  onClick={() => setOpen(false)}
                  className="p-1 rounded hover:bg-accent transition-colors"
                  aria-label="Close"
                >
                  <X className="h-3.5 w-3.5 text-muted-foreground" />
                </button>
              </div>
            </div>

            {/* Messages / empty state */}
            <div className="flex-1 overflow-y-auto px-4 py-3 space-y-3 min-h-[160px]">
              {messages.length === 0 ? (
                <div className="space-y-2 pt-1">
                  <p className="text-xs text-muted-foreground">
                    Ask me anything about the app:
                  </p>
                  {SUGGESTED.map((s) => (
                    <button
                      key={s}
                      type="button"
                      onClick={() => void ask(s)}
                      className="w-full text-left text-xs bg-primary/5 border border-primary/20 rounded-lg px-3 py-2 hover:bg-primary/10 transition-colors text-primary"
                    >
                      {s}
                    </button>
                  ))}
                </div>
              ) : (
                messages.map((m) => (
                  <div
                    key={m.id}
                    className={`text-xs leading-relaxed rounded-xl px-3 py-2 max-w-[90%] ${
                      m.role === "user"
                        ? "bg-primary text-primary-foreground ml-auto"
                        : "bg-muted text-foreground"
                    }`}
                  >
                    {m.content ? (
                      m.content
                    ) : (
                      <Loader2 className="h-3 w-3 animate-spin text-muted-foreground" />
                    )}
                  </div>
                ))
              )}
              <div ref={bottomRef} />
            </div>

            {/* Footer disclaimer */}
            <p className="text-[9px] text-muted-foreground text-center pb-1 px-3 shrink-0">
              Not medical advice. Research use only.
            </p>

            {/* Composer */}
            <div className="px-3 pb-3 shrink-0">
              <div className="flex gap-1.5 items-center">
                <input
                  ref={inputRef}
                  type="text"
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={handleKey}
                  disabled={isLoading}
                  placeholder="Type a question…"
                  aria-label="Help question"
                  className="flex-1 h-8 text-xs rounded-lg border border-input bg-background px-3 focus:outline-none focus:ring-2 focus:ring-ring disabled:opacity-60 placeholder:text-muted-foreground"
                />
                <Button
                  type="button"
                  size="icon"
                  className="h-8 w-8 shrink-0"
                  onClick={submit}
                  disabled={isLoading || !input.trim()}
                  aria-label="Send"
                >
                  {isLoading ? (
                    <Loader2 className="h-3.5 w-3.5 animate-spin" />
                  ) : (
                    <Send className="h-3.5 w-3.5" />
                  )}
                </Button>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Floating trigger button */}
      <motion.button
        type="button"
        onClick={() => setOpen((o) => !o)}
        whileHover={{ scale: 1.08 }}
        whileTap={{ scale: 0.95 }}
        aria-label={open ? "Close help" : "Open help"}
        aria-expanded={open}
        className="h-11 w-11 rounded-full bg-primary text-primary-foreground shadow-lg flex items-center justify-center hover:bg-primary/90 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
      >
        <HelpCircle className="h-5 w-5" />
      </motion.button>
    </div>
  );
}
