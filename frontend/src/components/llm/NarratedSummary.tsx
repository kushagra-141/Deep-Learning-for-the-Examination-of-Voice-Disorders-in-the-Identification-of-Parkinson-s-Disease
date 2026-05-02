import { Loader2, Sparkles } from "lucide-react";
import { useReportNarration } from "../../hooks/useReportNarration";

interface NarratedSummaryProps {
  predictionId: string | undefined;
  /** Auto-trigger the load on mount rather than waiting for an explicit call. */
  autoLoad?: boolean;
}

/**
 * Shows an LLM-generated narrative paragraph for inclusion above the PDF
 * download button. Loads on mount when ``autoLoad`` is true; otherwise the
 * parent controls timing by checking ``status`` and calling ``load()``.
 */
export function NarratedSummary({ predictionId, autoLoad = true }: NarratedSummaryProps) {
  const { narrative, status, load } = useReportNarration(predictionId);

  // Kick off the load if auto.
  if (autoLoad && status === "idle" && predictionId) {
    void load();
  }

  if (status === "idle" || status === "loading") {
    return (
      <div className="flex items-center gap-2 text-xs text-muted-foreground py-2">
        <Loader2 className="h-3.5 w-3.5 animate-spin" />
        Generating report narrative…
      </div>
    );
  }

  if (!narrative) return null;

  return (
    <div className="rounded-md border bg-primary/5 p-3 space-y-1.5">
      <p className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground flex items-center gap-1">
        <Sparkles className="h-3 w-3 text-primary" />
        AI Narrative
      </p>
      <p className="text-xs leading-relaxed text-foreground/90">{narrative}</p>
    </div>
  );
}
