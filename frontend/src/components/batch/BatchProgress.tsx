import { motion } from "framer-motion";
import { CheckCircle2, Clock, Loader2, XCircle } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import { Badge } from "../ui/badge";
import type { BatchJobStatus } from "../../api/client";

const STATUS_META: Record<BatchJobStatus["status"], { label: string; icon: React.ElementType; tone: string }> = {
  queued: { label: "Queued", icon: Clock, tone: "text-muted-foreground" },
  running: { label: "Running", icon: Loader2, tone: "text-primary" },
  succeeded: { label: "Succeeded", icon: CheckCircle2, tone: "text-success" },
  failed: { label: "Failed", icon: XCircle, tone: "text-destructive" },
};

interface BatchProgressProps {
  status: BatchJobStatus;
  filename?: string;
}

export function BatchProgress({ status, filename }: BatchProgressProps) {
  const meta = STATUS_META[status.status];
  const Icon = meta.icon;
  const pct = Math.round(status.progress * 100);
  const isRunning = status.status === "running" || status.status === "queued";

  return (
    <Card>
      <CardHeader className="pb-2">
        <div className="flex items-start justify-between gap-2">
          <div>
            <CardTitle className="text-sm flex items-center gap-2">
              <Icon
                className={`h-4 w-4 ${meta.tone} ${status.status === "running" ? "animate-spin" : ""}`}
              />
              <span>Batch job</span>
              <Badge variant="outline" className="text-[10px] font-mono normal-case">
                {status.id.slice(0, 8)}
              </Badge>
            </CardTitle>
            {filename && (
              <p className="text-xs text-muted-foreground mt-0.5 truncate" title={filename}>
                {filename}
              </p>
            )}
          </div>
          <Badge
            variant={status.status === "failed" ? "destructive" : "outline"}
            className="capitalize"
          >
            {meta.label}
          </Badge>
        </div>
      </CardHeader>
      <CardContent className="space-y-3">
        <div className="space-y-1.5">
          <div className="flex justify-between text-xs">
            <span className="text-muted-foreground">
              {status.row_count > 0
                ? `${Math.round(status.progress * status.row_count)} / ${status.row_count} rows`
                : "Initializing…"}
            </span>
            <span className="font-mono font-bold tabular-nums">{pct}%</span>
          </div>
          <div className="h-2 w-full bg-muted rounded-full overflow-hidden">
            <motion.div
              className={`h-full rounded-full ${
                status.status === "failed" ? "bg-destructive" : "bg-primary"
              }`}
              initial={{ width: 0 }}
              animate={{ width: `${pct}%` }}
              transition={{ duration: 0.4, ease: "easeOut" }}
            />
            {isRunning && pct < 5 && (
              <motion.div
                className="h-full bg-primary/40"
                initial={{ width: "0%" }}
                animate={{ width: ["0%", "30%", "0%"] }}
                transition={{ duration: 1.5, repeat: Infinity }}
              />
            )}
          </div>
        </div>
        {status.error && (
          <p className="text-xs text-destructive bg-destructive/10 rounded-md p-2 font-mono">
            {status.error}
          </p>
        )}
      </CardContent>
    </Card>
  );
}
