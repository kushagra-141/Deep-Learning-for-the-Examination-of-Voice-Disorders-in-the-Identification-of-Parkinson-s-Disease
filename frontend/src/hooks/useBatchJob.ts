import { useEffect, useRef, useState } from "react";
import { batchDownloadUrl, getBatchStatus, submitBatch, type BatchJobStatus } from "../api/client";

type Phase =
  | { kind: "idle" }
  | { kind: "uploading"; filename: string }
  | { kind: "polling"; jobId: string; filename: string; status: BatchJobStatus }
  | { kind: "done"; jobId: string; filename: string; status: BatchJobStatus }
  | { kind: "error"; message: string; filename?: string };

const POLL_INTERVAL_MS = 1500;

export function useBatchJob() {
  const [phase, setPhase] = useState<Phase>({ kind: "idle" });
  const cancelledRef = useRef(false);

  useEffect(() => () => {
    cancelledRef.current = true;
  }, []);

  const submit = async (file: File) => {
    cancelledRef.current = false;
    setPhase({ kind: "uploading", filename: file.name });
    try {
      const created = await submitBatch(file);
      const initialStatus: BatchJobStatus = {
        id: created.job_id,
        status: "queued",
        progress: 0,
        row_count: 0,
        error: null,
      };
      setPhase({ kind: "polling", jobId: created.job_id, filename: file.name, status: initialStatus });
      void poll(created.job_id, file.name);
    } catch (err) {
      const message = err instanceof Error ? err.message : "Upload failed";
      setPhase({ kind: "error", message, filename: file.name });
    }
  };

  const poll = async (jobId: string, filename: string) => {
    while (!cancelledRef.current) {
      try {
        const status = await getBatchStatus(jobId);
        if (cancelledRef.current) return;
        if (status.status === "succeeded") {
          setPhase({ kind: "done", jobId, filename, status });
          return;
        }
        if (status.status === "failed") {
          setPhase({
            kind: "error",
            message: status.error || "Batch job failed",
            filename,
          });
          return;
        }
        setPhase({ kind: "polling", jobId, filename, status });
      } catch (err) {
        const message = err instanceof Error ? err.message : "Status check failed";
        setPhase({ kind: "error", message, filename });
        return;
      }
      await new Promise((resolve) => setTimeout(resolve, POLL_INTERVAL_MS));
    }
  };

  const reset = () => {
    cancelledRef.current = true;
    setPhase({ kind: "idle" });
    // Re-enable polling for the next submission.
    setTimeout(() => {
      cancelledRef.current = false;
    }, 0);
  };

  const downloadUrl = phase.kind === "done" ? batchDownloadUrl(phase.jobId) : null;

  return { phase, submit, reset, downloadUrl };
}
