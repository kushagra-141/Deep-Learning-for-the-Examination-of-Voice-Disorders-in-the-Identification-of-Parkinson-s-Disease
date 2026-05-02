import { motion, AnimatePresence } from "framer-motion";
import { Clock, Trash2, FlaskConical, Mic, FileSpreadsheet } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../ui/card";
import { Badge } from "../ui/badge";
import { Button } from "../ui/button";
import { useRecentPredictions, type RecentPrediction } from "../../stores/recent";

const MODE_ICON: Record<RecentPrediction["inputMode"], React.ElementType> = {
  manual: FlaskConical,
  audio: Mic,
  batch: FileSpreadsheet,
};

function riskClasses(label: RecentPrediction["riskLabel"]) {
  if (label === "High Risk") return { dot: "bg-destructive", text: "text-destructive" };
  if (label === "Borderline") return { dot: "bg-warning", text: "text-warning" };
  return { dot: "bg-success", text: "text-success" };
}

function relativeTime(iso: string): string {
  const then = new Date(iso).getTime();
  const diff = Date.now() - then;
  if (Number.isNaN(then)) return "—";
  const m = Math.round(diff / 60_000);
  if (m < 1) return "just now";
  if (m < 60) return `${m}m ago`;
  const h = Math.round(m / 60);
  if (h < 24) return `${h}h ago`;
  const d = Math.round(h / 24);
  return `${d}d ago`;
}

interface RecentListProps {
  /**
   * Called when a recent entry is clicked. Receives the saved feature snapshot
   * so the parent can restore the form state (and optionally re-run prediction).
   */
  onRestore?: (entry: RecentPrediction) => void;
  className?: string;
}

export function RecentList({ onRestore, className }: RecentListProps) {
  const items = useRecentPredictions((s) => s.items);
  const remove = useRecentPredictions((s) => s.remove);
  const clear = useRecentPredictions((s) => s.clear);

  if (items.length === 0) {
    return (
      <Card className={className}>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm font-semibold uppercase tracking-wider text-muted-foreground flex items-center gap-2">
            <Clock className="h-3 w-3" />
            Recent Predictions
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-xs text-muted-foreground">
            Your last 10 predictions will appear here. Nothing yet — run one to get started.
          </p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className={className}>
      <CardHeader className="pb-2">
        <div className="flex items-start justify-between gap-2">
          <div>
            <CardTitle className="text-sm font-semibold uppercase tracking-wider text-muted-foreground flex items-center gap-2">
              <Clock className="h-3 w-3" />
              Recent Predictions
            </CardTitle>
            <CardDescription className="text-[11px] mt-0.5">
              Click an entry to restore the form. Stored locally on this device.
            </CardDescription>
          </div>
          <Button
            type="button"
            variant="ghost"
            size="sm"
            className="h-7 text-[11px]"
            onClick={clear}
            aria-label="Clear recent predictions"
          >
            Clear
          </Button>
        </div>
      </CardHeader>
      <CardContent className="space-y-1.5">
        <AnimatePresence initial={false}>
          {items.map((entry) => {
            const risk = riskClasses(entry.riskLabel);
            const Icon = MODE_ICON[entry.inputMode];
            const key = entry.predictionId || entry.createdAt;
            return (
              <motion.button
                key={key}
                type="button"
                onClick={() => onRestore?.(entry)}
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: "auto" }}
                exit={{ opacity: 0, height: 0 }}
                transition={{ duration: 0.18 }}
                className="w-full text-left rounded-md border border-border/50 bg-card hover:bg-accent transition-colors p-2 group focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              >
                <div className="flex items-center gap-2">
                  <span
                    className={`h-2 w-2 rounded-full shrink-0 ${risk.dot}`}
                    aria-hidden="true"
                  />
                  <Icon className="h-3 w-3 text-muted-foreground shrink-0" aria-hidden="true" />
                  <span className={`text-xs font-mono font-bold tabular-nums shrink-0 ${risk.text}`}>
                    {(entry.probability * 100).toFixed(1)}%
                  </span>
                  <Badge variant="outline" className="text-[9px] px-1.5 py-0 font-normal capitalize">
                    {entry.inputMode}
                  </Badge>
                  <span className="text-[10px] text-muted-foreground ml-auto shrink-0">
                    {relativeTime(entry.createdAt)}
                  </span>
                  <span
                    role="button"
                    tabIndex={0}
                    aria-label="Remove from recent"
                    onClick={(e) => {
                      e.stopPropagation();
                      remove(entry.predictionId);
                    }}
                    onKeyDown={(e) => {
                      if (e.key === "Enter" || e.key === " ") {
                        e.preventDefault();
                        e.stopPropagation();
                        remove(entry.predictionId);
                      }
                    }}
                    className="opacity-0 group-hover:opacity-100 focus:opacity-100 transition-opacity p-1 rounded hover:bg-destructive/10 hover:text-destructive cursor-pointer"
                  >
                    <Trash2 className="h-3 w-3" />
                  </span>
                </div>
              </motion.button>
            );
          })}
        </AnimatePresence>
      </CardContent>
    </Card>
  );
}
