import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { AlertTriangle, Download, FileDown, Loader2 } from "lucide-react";
import { Button } from "../ui/button";
import { downloadReport } from "../../lib/pdf/ReportDocument";
import { getOrCreateNarrative } from "../../api/client";
import type { PredictionResponse } from "../../api/client";

const NARRATIVE_PLACEHOLDER = "Narrative unavailable for this report.";

interface DownloadReportButtonProps {
  prediction: PredictionResponse;
  features: Record<string, number>;
  /** Optional pre-fetched narrative; if omitted the button fetches it. */
  narrative?: string | null | undefined;
  className?: string;
}

export function DownloadReportButton({
  prediction,
  features,
  narrative: narrativeProp,
  className,
}: DownloadReportButtonProps) {
  const [status, setStatus] = useState<"idle" | "rendering" | "done" | "failed">("idle");

  const handleClick = async () => {
    if (status === "rendering") return;
    setStatus("rendering");
    try {
      // Fetch narration if it wasn't passed in and the prediction has a real id.
      let narrative = narrativeProp ?? null;
      if (narrative === null && prediction.prediction_id) {
        try {
          const result = await getOrCreateNarrative(prediction.prediction_id);
          narrative = result.narrative;
        } catch {
          narrative = NARRATIVE_PLACEHOLDER;
        }
      }
      const stamp = new Date().toISOString().replace(/[:.]/g, "-").slice(0, 19);
      await downloadReport(
        { prediction, features, narrative },
        `parkinsons-report_${stamp}.pdf`,
      );
      setStatus("done");
    } catch (err) {
      console.error("PDF generation failed:", err);
      setStatus("failed");
    } finally {
      setTimeout(() => setStatus("idle"), 2200);
    }
  };

  return (
    <Button
      type="button"
      variant="outline"
      className={className}
      onClick={handleClick}
      disabled={status === "rendering"}
      aria-label="Download a PDF report of this prediction"
    >
      <AnimatePresence mode="wait" initial={false}>
        {status === "rendering" ? (
          <motion.span
            key="rendering"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="flex items-center"
          >
            <Loader2 className="h-4 w-4 mr-2 animate-spin" />
            Generating…
          </motion.span>
        ) : status === "done" ? (
          <motion.span
            key="done"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="flex items-center text-success"
          >
            <FileDown className="h-4 w-4 mr-2" />
            Downloaded
          </motion.span>
        ) : status === "failed" ? (
          <motion.span
            key="failed"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="flex items-center text-destructive"
          >
            <AlertTriangle className="h-4 w-4 mr-2" />
            Generation failed
          </motion.span>
        ) : (
          <motion.span
            key="idle"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="flex items-center"
          >
            <Download className="h-4 w-4 mr-2" />
            Download report
          </motion.span>
        )}
      </AnimatePresence>
    </Button>
  );
}
