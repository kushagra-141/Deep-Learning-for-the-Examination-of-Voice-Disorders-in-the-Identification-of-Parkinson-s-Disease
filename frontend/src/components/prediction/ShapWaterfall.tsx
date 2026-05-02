import { useMemo, useState } from "react";
import { motion } from "framer-motion";
import { ChevronDown, ChevronUp, Sparkles } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../ui/card";
import { Badge } from "../ui/badge";
import { Button } from "../ui/button";
import type { ShapContribution } from "../../api/client";

interface ShapWaterfallProps {
  contributions: ShapContribution[];
  primaryModel: string;
  baseValue?: number;
  className?: string;
}

/**
 * SHAP waterfall chart.
 *
 * Shows the top-5 features by |shap| by default; "Show all 22" toggle reveals
 * the full set. Bars diverge from a center axis: positive (push toward PD)
 * flow right in destructive color, negative flow left in success color.
 */
export function ShapWaterfall({ contributions, primaryModel, baseValue, className }: ShapWaterfallProps) {
  const [showAll, setShowAll] = useState(false);

  const sorted = useMemo(
    () => [...contributions].sort((a, b) => Math.abs(b.shap) - Math.abs(a.shap)),
    [contributions],
  );

  const visible = showAll ? sorted : sorted.slice(0, 5);
  const maxAbs = Math.max(...sorted.map((c) => Math.abs(c.shap)), 1e-9);
  const totalShap = sorted.reduce((acc, c) => acc + c.shap, 0);
  const finalLogit = (baseValue ?? 0) + totalShap;

  return (
    <Card className={className}>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-semibold uppercase tracking-wider text-muted-foreground flex items-center gap-2">
          <Sparkles className="h-3 w-3 text-primary" />
          SHAP Waterfall
          <Badge variant="outline" className="ml-auto text-[10px] font-mono normal-case">
            {primaryModel.replace(/_/g, " ")}
          </Badge>
        </CardTitle>
        <CardDescription className="text-xs">
          Per-feature contribution to the prediction logit. Red pushes toward Parkinson's; green pushes toward healthy.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-3">
        <div className="space-y-1.5">
          {visible.map((c, i) => {
            const pct = (Math.abs(c.shap) / maxAbs) * 100;
            const positive = c.shap >= 0;
            return (
              <motion.div
                key={c.feature}
                initial={{ opacity: 0, x: -8 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.04 * i, duration: 0.25 }}
                className="grid grid-cols-[8rem_1fr_4rem] items-center gap-2"
              >
                <div className="min-w-0">
                  <div
                    className="text-[11px] font-mono text-foreground truncate"
                    title={c.feature}
                  >
                    {c.feature}
                  </div>
                  <div className="text-[9px] font-mono text-muted-foreground tabular-nums">
                    = {Number.isFinite(c.value) ? c.value.toFixed(4) : "—"}
                  </div>
                </div>

                <div className="relative flex items-center h-3">
                  <div className="absolute inset-0 flex items-center">
                    <div className="flex-1 flex justify-end">
                      {!positive && (
                        <motion.div
                          className="h-2.5 rounded-l-sm bg-success"
                          initial={{ width: 0 }}
                          animate={{ width: `${pct}%` }}
                          transition={{ duration: 0.45, delay: 0.08 + 0.04 * i, ease: "easeOut" }}
                        />
                      )}
                    </div>
                    <div className="w-px h-full bg-border mx-0.5" aria-hidden="true" />
                    <div className="flex-1">
                      {positive && (
                        <motion.div
                          className="h-2.5 rounded-r-sm bg-destructive"
                          initial={{ width: 0 }}
                          animate={{ width: `${pct}%` }}
                          transition={{ duration: 0.45, delay: 0.08 + 0.04 * i, ease: "easeOut" }}
                        />
                      )}
                    </div>
                  </div>
                </div>

                <span
                  className={`text-[11px] font-mono font-bold text-right tabular-nums ${
                    positive ? "text-destructive" : "text-success"
                  }`}
                >
                  {positive ? "+" : ""}
                  {c.shap.toFixed(2)}
                </span>
              </motion.div>
            );
          })}
        </div>

        {sorted.length > 5 && (
          <Button
            type="button"
            variant="ghost"
            size="sm"
            className="w-full text-xs"
            onClick={() => setShowAll((s) => !s)}
            aria-expanded={showAll}
          >
            {showAll ? (
              <>
                <ChevronUp className="h-3 w-3 mr-1.5" />
                Show top 5
              </>
            ) : (
              <>
                <ChevronDown className="h-3 w-3 mr-1.5" />
                Show all {sorted.length}
              </>
            )}
          </Button>
        )}

        {baseValue !== undefined && (
          <div className="pt-2 border-t flex items-center justify-between text-[10px] font-mono text-muted-foreground tabular-nums">
            <span>base logit: {baseValue.toFixed(2)}</span>
            <span>Σ shap: {totalShap >= 0 ? "+" : ""}{totalShap.toFixed(2)}</span>
            <span className="text-foreground">
              final: {finalLogit.toFixed(2)}
            </span>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
