import { useCallback, useRef, useState } from "react";
import { askHelp } from "../api/client";

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
}

type HelpStatus = "idle" | "loading" | "error";

const FRESH_ID = () =>
  typeof crypto !== "undefined" && "randomUUID" in crypto
    ? crypto.randomUUID()
    : `help-${Date.now()}-${Math.random().toString(16).slice(2)}`;

export function useHelpBot() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [status, setStatus] = useState<HelpStatus>("idle");
  const inflightRef = useRef(false);

  const ask = useCallback(async (question: string) => {
    const text = question.trim();
    if (!text || inflightRef.current) return;
    inflightRef.current = true;
    const userMsgId = FRESH_ID();
    const assistantMsgId = FRESH_ID();

    setMessages((prev) => [
      ...prev,
      { id: userMsgId, role: "user", content: text },
      { id: assistantMsgId, role: "assistant", content: "" },
    ]);
    setStatus("loading");

    try {
      const result = await askHelp(text);
      setMessages((prev) =>
        prev.map((m) =>
          m.id === assistantMsgId ? { ...m, content: result.answer } : m,
        ),
      );
      setStatus("idle");
    } catch (err) {
      const message = err instanceof Error ? err.message : "Request failed";
      setMessages((prev) =>
        prev.map((m) =>
          m.id === assistantMsgId ? { ...m, content: `Error: ${message}` } : m,
        ),
      );
      setStatus("error");
    } finally {
      inflightRef.current = false;
    }
  }, []);

  const reset = useCallback(() => {
    setMessages([]);
    setStatus("idle");
    inflightRef.current = false;
  }, []);

  return { messages, status, ask, reset };
}
