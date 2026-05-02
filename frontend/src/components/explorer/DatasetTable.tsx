import { motion } from "framer-motion";
import type { PCAPoint } from "../../api/client";

interface Row extends PCAPoint {
  index: number;
  inBrush: boolean;
}

interface DatasetTableProps {
  rows: Row[];
  totalRows: number;
}

export function DatasetTable({ rows, totalRows }: DatasetTableProps) {
  const filtered = rows.filter((r) => r.inBrush);
  const visible = filtered.length > 0 ? filtered : rows;
  const isFiltered = filtered.length > 0 && filtered.length !== rows.length;

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between text-xs">
        <span className="text-muted-foreground">
          Showing {visible.length} of {totalRows} dataset rows
          {isFiltered && (
            <span className="ml-2 inline-flex items-center gap-1 text-primary font-medium">
              <span className="h-1.5 w-1.5 rounded-full bg-primary" />
              brush filter active
            </span>
          )}
        </span>
      </div>
      <div className="border rounded-md overflow-hidden">
        <div className="grid grid-cols-[3rem_1fr_1fr_5rem] text-[11px] font-semibold uppercase tracking-wider text-muted-foreground bg-muted/50 px-3 py-2 border-b">
          <span>#</span>
          <span>PC1</span>
          <span>PC2</span>
          <span className="text-right">Class</span>
        </div>
        <div className="max-h-[320px] overflow-y-auto">
          {visible.slice(0, 200).map((r, i) => (
            <motion.div
              key={r.index}
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ duration: 0.15, delay: Math.min(i * 0.005, 0.5) }}
              className="grid grid-cols-[3rem_1fr_1fr_5rem] text-xs px-3 py-1.5 border-b last:border-b-0 hover:bg-accent/50 font-mono tabular-nums"
            >
              <span className="text-muted-foreground">{r.index + 1}</span>
              <span>{r.x.toFixed(4)}</span>
              <span>{r.y.toFixed(4)}</span>
              <span
                className={`text-right font-bold ${
                  r.label === 1 ? "text-destructive" : "text-success"
                }`}
              >
                {r.label === 1 ? "PD" : "HC"}
              </span>
            </motion.div>
          ))}
          {visible.length > 200 && (
            <p className="text-[10px] text-muted-foreground text-center py-2 border-t">
              + {visible.length - 200} more rows (truncated for display)
            </p>
          )}
        </div>
      </div>
    </div>
  );
}
