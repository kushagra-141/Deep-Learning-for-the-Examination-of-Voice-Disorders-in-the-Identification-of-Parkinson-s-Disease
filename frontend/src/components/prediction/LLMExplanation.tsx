import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Bot, Sparkles, AlertTriangle, Loader2 } from "lucide-react";
import { Button } from "../ui/button";
import { Card, CardContent } from "../ui/card";
import { streamExplanation } from "../../api/client";

interface LLMExplanationProps {
  features: Record<string, number>;
  probability: number;
  inputMode: "manual" | "audio" | "batch";
}

export function LLMExplanation({ features, probability, inputMode }: LLMExplanationProps) {
  const [explanation, setExplanation] = useState("");
  const [isGenerating, setIsGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleGenerate = async () => {
    setExplanation("");
    setError(null);
    setIsGenerating(true);

    try {
      const stream = streamExplanation(features, probability, inputMode);
      for await (const chunk of stream) {
        setExplanation((prev) => prev + chunk);
      }
    } catch (err: any) {
      console.error("Explanation error:", err);
      setError(err.message || "Failed to generate explanation. Ensure API key is configured.");
    } finally {
      setIsGenerating(false);
    }
  };

  // Basic markdown bold/italic parser for the streamed text
  const renderFormattedText = (text: string) => {
    if (!text) return null;
    
    // Quick hack to parse basic markdown since we don't have react-markdown installed
    // Split by newlines for paragraphs
    const paragraphs = text.split("\n").filter(p => p.trim() !== "");
    
    return paragraphs.map((p, i) => {
      // Very basic bold handling for `**text**`
      const boldParts = p.split(/\*\*(.*?)\*\*/g);
      
      return (
        <p key={i} className="mb-3 leading-relaxed text-sm">
          {boldParts.map((part, j) => 
            j % 2 === 1 ? <strong key={j} className="text-foreground">{part}</strong> : part
          )}
        </p>
      );
    });
  };

  return (
    <div className="w-full mt-4 space-y-4">
      {!explanation && !isGenerating && !error && (
        <Button
          variant="outline"
          className="w-full border-dashed bg-muted/20 hover:bg-muted/50 transition-colors group"
          onClick={handleGenerate}
        >
          <Bot className="h-4 w-4 mr-2 text-primary group-hover:scale-110 transition-transform" />
          <span className="bg-gradient-to-r from-primary to-violet-500 bg-clip-text text-transparent font-semibold">
            Explain this result with AI
          </span>
          <Sparkles className="h-4 w-4 ml-2 text-violet-500 opacity-70" />
        </Button>
      )}

      <AnimatePresence>
        {(explanation || isGenerating || error) && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            className="overflow-hidden"
          >
            <Card className="border-primary/20 bg-primary/5 shadow-inner">
              <CardContent className="p-5">
                <div className="flex items-center gap-2 mb-3 font-semibold text-primary">
                  <Bot className="h-5 w-5" />
                  AI Analysis
                  {isGenerating && <Loader2 className="h-4 w-4 ml-2 animate-spin text-muted-foreground" />}
                </div>
                
                {error ? (
                  <div className="text-sm text-destructive flex items-center gap-2 p-3 bg-destructive/10 rounded-md">
                    <AlertTriangle className="h-4 w-4" />
                    {error}
                  </div>
                ) : (
                  <div className="text-muted-foreground text-sm max-w-prose">
                    {renderFormattedText(explanation)}
                  </div>
                )}
              </CardContent>
            </Card>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
