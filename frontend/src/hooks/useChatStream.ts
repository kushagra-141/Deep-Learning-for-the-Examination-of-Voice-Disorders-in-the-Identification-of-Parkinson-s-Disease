import { useCallback, useEffect, useRef, useState } from "react";
import { API_BASE_URL } from "../api/client";
import { parseSseStream } from "../lib/sse";
import type {
  ChatChunkOut,
  ChatFeature,
  ChatReadyEvent,
  ToolBadge,
  UiMessage,
} from "../lib/schemas/chat";

type ChatStatus = "idle" | "streaming" | "error";

interface UseChatStreamOptions {
  predictionId?: string;
  feature?: ChatFeature;
}

interface UseChatStreamResult {
  messages: UiMessage[];
  status: ChatStatus;
  sessionId: string | null;
  send: (text: string) => Promise<void>;
  stop: () => void;
  reset: () => void;
}

const FRESH_ID = () =>
  typeof crypto !== "undefined" && "randomUUID" in crypto
    ? crypto.randomUUID()
    : `local-${Date.now()}-${Math.random().toString(16).slice(2, 8)}`;

/**
 * Drive a SSE-streamed chat conversation against `/api/v1/chat`.
 *
 * Aborts the in-flight stream on unmount so we don't leak network calls when
 * the drawer closes mid-reply. Tool calls render as inline badges on the
 * assistant bubble that produced them.
 */
export function useChatStream({
  predictionId,
  feature = "explainer",
}: UseChatStreamOptions = {}): UseChatStreamResult {
  const [messages, setMessages] = useState<UiMessage[]>([]);
  const [status, setStatus] = useState<ChatStatus>("idle");
  const [sessionId, setSessionId] = useState<string | null>(null);

  const controllerRef = useRef<AbortController | null>(null);

  // Abort any in-flight stream on unmount.
  useEffect(() => {
    return () => {
      controllerRef.current?.abort();
      controllerRef.current = null;
    };
  }, []);

  const stop = useCallback(() => {
    controllerRef.current?.abort();
    controllerRef.current = null;
    setStatus("idle");
  }, []);

  const reset = useCallback(() => {
    stop();
    setMessages([]);
    setSessionId(null);
  }, [stop]);

  const send = useCallback(
    async (text: string) => {
      const userMessage = text.trim();
      if (!userMessage) return;

      controllerRef.current?.abort();
      const controller = new AbortController();
      controllerRef.current = controller;

      const userMsgId = FRESH_ID();
      const assistantId = FRESH_ID();
      const tools: ToolBadge[] = [];

      setMessages((prev) => [
        ...prev,
        { id: userMsgId, role: "user", content: userMessage },
        { id: assistantId, role: "assistant", content: "", streaming: true, tools: [] },
      ]);
      setStatus("streaming");

      const body = {
        session_id: sessionId ?? undefined,
        prediction_id: predictionId,
        message: userMessage,
        feature,
      };

      let response: Response;
      try {
        response = await fetch(`${API_BASE_URL}/chat/`, {
          method: "POST",
          credentials: "include",
          headers: {
            "Content-Type": "application/json",
            Accept: "text/event-stream",
          },
          body: JSON.stringify(body),
          signal: controller.signal,
        });
      } catch (err) {
        const message = err instanceof Error ? err.message : "network error";
        setMessages((prev) =>
          prev.map((m) =>
            m.id === assistantId
              ? { ...m, content: "Connection failed: " + message, streaming: false }
              : m,
          ),
        );
        setStatus("error");
        return;
      }

      if (!response.ok || !response.body) {
        const detail = response.ok ? "empty stream" : `HTTP ${response.status}`;
        setMessages((prev) =>
          prev.map((m) =>
            m.id === assistantId
              ? { ...m, content: `Failed to start chat (${detail}).`, streaming: false }
              : m,
          ),
        );
        setStatus("error");
        return;
      }

      try {
        for await (const evt of parseSseStream<ChatChunkOut | ChatReadyEvent>(
          response.body,
        )) {
          if (evt.event === "ready" && evt.data && "session_id" in evt.data) {
            setSessionId(evt.data.session_id);
            continue;
          }
          if (!evt.data || !("type" in evt.data)) continue;
          const chunk = evt.data;
          switch (chunk.type) {
            case "delta": {
              if (!chunk.delta_text) break;
              setMessages((prev) =>
                prev.map((m) =>
                  m.id === assistantId
                    ? { ...m, content: m.content + chunk.delta_text }
                    : m,
                ),
              );
              break;
            }
            case "tool": {
              if (!chunk.tool_name) break;
              const status = chunk.tool_status ?? "called";
              tools.push({
                name: chunk.tool_name,
                status,
                detail: chunk.tool_detail ?? null,
              });
              setMessages((prev) =>
                prev.map((m) =>
                  m.id === assistantId ? { ...m, tools: [...tools] } : m,
                ),
              );
              break;
            }
            case "done": {
              setMessages((prev) =>
                prev.map((m) =>
                  m.id === assistantId ? { ...m, streaming: false } : m,
                ),
              );
              setStatus("idle");
              break;
            }
            case "error": {
              setMessages((prev) =>
                prev.map((m) =>
                  m.id === assistantId
                    ? {
                        ...m,
                        content: m.content + (m.content ? "\n\n" : "") + (chunk.error || "Error"),
                        streaming: false,
                      }
                    : m,
                ),
              );
              setStatus("error");
              break;
            }
          }
        }
      } catch (err) {
        if ((err as DOMException)?.name === "AbortError") {
          setMessages((prev) =>
            prev.map((m) =>
              m.id === assistantId ? { ...m, streaming: false } : m,
            ),
          );
          setStatus("idle");
          return;
        }
        const message = err instanceof Error ? err.message : "stream error";
        setMessages((prev) =>
          prev.map((m) =>
            m.id === assistantId
              ? { ...m, content: m.content + "\n\n[stream error] " + message, streaming: false }
              : m,
          ),
        );
        setStatus("error");
      } finally {
        if (controllerRef.current === controller) controllerRef.current = null;
      }
    },
    [feature, predictionId, sessionId],
  );

  return { messages, status, sessionId, send, stop, reset };
}
