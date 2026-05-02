import { useEffect, useRef } from "react";
import * as Dialog from "@radix-ui/react-dialog";
import { motion } from "framer-motion";
import { AlertTriangle, MessageSquare, RotateCcw, X } from "lucide-react";
import { Badge } from "../ui/badge";
import { Button } from "../ui/button";
import { ChatMessage } from "./ChatMessage";
import { ChatComposer } from "./ChatComposer";
import { useChatStream } from "../../hooks/useChatStream";
import type { PredictionResponse } from "../../api/client";

interface ChatSidebarProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  prediction: PredictionResponse;
}

function buildSuggestedQuestions(prediction: PredictionResponse): string[] {
  const label = prediction.ensemble.probability >= 0.5 ? "Parkinson's" : "healthy";
  const topFeature = prediction.ensemble.shap_top?.[0]?.feature ?? "PPE";
  return [
    `Why did the model predict ${label}?`,
    `What does ${topFeature} measure?`,
    `What if my ${topFeature} was different?`,
  ];
}

export function ChatSidebar({ open, onOpenChange, prediction }: ChatSidebarProps) {
  const { messages, status, send, stop, reset } = useChatStream({
    predictionId: prediction.prediction_id,
    feature: "explainer",
  });

  const bottomRef = useRef<HTMLDivElement>(null);
  const isStreaming = status === "streaming";
  const suggested = buildSuggestedQuestions(prediction);

  // Scroll to the latest message whenever messages change.
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // Reset the conversation when the drawer opens for a new prediction.
  useEffect(() => {
    if (open) reset();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open, prediction.prediction_id]);

  const riskLabel =
    prediction.ensemble.probability >= 0.7
      ? "High Risk"
      : prediction.ensemble.probability >= 0.4
        ? "Borderline"
        : "Low Risk";

  return (
    <Dialog.Root open={open} onOpenChange={onOpenChange}>
      <Dialog.Portal>
        <Dialog.Overlay asChild>
          <motion.div
            className="fixed inset-0 bg-black/40 backdrop-blur-sm z-50"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
          />
        </Dialog.Overlay>

        <Dialog.Content asChild>
          <motion.div
            className="fixed inset-y-0 right-0 z-50 flex flex-col w-full max-w-md bg-background border-l shadow-2xl focus:outline-none"
            initial={{ x: "100%" }}
            animate={{ x: 0 }}
            exit={{ x: "100%" }}
            transition={{ type: "spring", stiffness: 300, damping: 30 }}
            aria-label="AI Result Explainer"
          >
            {/* Header */}
            <div className="flex items-center justify-between px-4 py-3 border-b shrink-0">
              <div className="flex items-center gap-2 min-w-0">
                <MessageSquare className="h-4 w-4 text-primary shrink-0" />
                <Dialog.Title className="font-semibold text-sm truncate">
                  Discuss this result
                </Dialog.Title>
                <Badge variant="outline" className="text-[10px] font-mono shrink-0">
                  {prediction.primary_model.replace(/_/g, " ")} ·{" "}
                  {(prediction.ensemble.probability * 100).toFixed(1)}% · {riskLabel}
                </Badge>
              </div>
              <div className="flex items-center gap-1 shrink-0">
                {messages.length > 0 && (
                  <Button
                    type="button"
                    variant="ghost"
                    size="sm"
                    className="h-7 text-xs"
                    onClick={reset}
                    aria-label="Clear conversation"
                  >
                    <RotateCcw className="h-3 w-3 mr-1" />
                    Clear
                  </Button>
                )}
                <Dialog.Close asChild>
                  <button
                    className="rounded-md p-1.5 hover:bg-accent transition-colors"
                    aria-label="Close"
                  >
                    <X className="h-4 w-4" />
                  </button>
                </Dialog.Close>
              </div>
            </div>

            {/* Messages */}
            <div
              className="flex-1 overflow-y-auto px-4 py-4 space-y-4"
              aria-live="polite"
              aria-label="Chat messages"
            >
              {messages.length === 0 && (
                <div className="flex flex-col items-center justify-center h-full gap-4 text-center px-4">
                  <MessageSquare className="h-10 w-10 text-muted-foreground/30" />
                  <div className="space-y-1">
                    <p className="text-sm font-medium">Ask about your prediction</p>
                    <p className="text-xs text-muted-foreground">
                      The assistant has access to your feature values, SHAP contributions,
                      and can run what-if simulations.
                    </p>
                  </div>
                  <div className="flex flex-col gap-2 w-full">
                    {suggested.map((q) => (
                      <button
                        key={q}
                        type="button"
                        onClick={() => send(q)}
                        className="text-left text-xs text-primary bg-primary/5 border border-primary/20 rounded-lg px-3 py-2 hover:bg-primary/10 transition-colors"
                      >
                        {q}
                      </button>
                    ))}
                  </div>
                </div>
              )}

              {messages.map((m) => (
                <ChatMessage key={m.id} message={m} />
              ))}

              {status === "error" && (
                <div className="flex items-start gap-2 text-xs text-destructive bg-destructive/10 rounded-md p-3">
                  <AlertTriangle className="h-3.5 w-3.5 shrink-0 mt-0.5" />
                  <span>The assistant is unavailable right now — try again in a minute.</span>
                </div>
              )}
              <div ref={bottomRef} />
            </div>

            {/* Composer */}
            <div className="px-4 py-3 border-t space-y-2 shrink-0">
              <ChatComposer onSend={send} onStop={stop} isStreaming={isStreaming} />
              <p className="text-[9px] text-muted-foreground text-center leading-relaxed">
                Research/educational use only — not a diagnostic tool. Consult a qualified
                neurologist for any medical concern.
              </p>
            </div>
          </motion.div>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}
