import { useCallback, useState } from "react";
import { getOrCreateNarrative } from "../api/client";

type NarrationStatus = "idle" | "loading" | "done" | "error";

const PLACEHOLDER =
  "Narrative unavailable for this report.";

export function useReportNarration(predictionId: string | undefined) {
  const [narrative, setNarrative] = useState<string | null>(null);
  const [status, setStatus] = useState<NarrationStatus>("idle");

  const load = useCallback(async () => {
    if (!predictionId || status === "loading" || narrative !== null) return;
    setStatus("loading");
    try {
      const result = await getOrCreateNarrative(predictionId);
      setNarrative(result.narrative);
      setStatus("done");
    } catch {
      setNarrative(PLACEHOLDER);
      setStatus("error");
    }
  }, [predictionId, status, narrative]);

  return { narrative, status, load, placeholder: PLACEHOLDER };
}
