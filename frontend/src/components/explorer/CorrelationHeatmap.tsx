import { useState } from "react";
import { Loader2 } from "lucide-react";
import type { CorrelationMatrix } from "../../api/client";

interface CorrelationHeatmapProps {
  data: CorrelationMatrix | undefined;
  isLoading: boolean;
}

function colorFor(value: number): string {
  // Diverging red (-1) → white (0) → blue (+1).
  const v = Math.max(-1, Math.min(1, value));
  if (v >= 0) {
    const alpha = v;
    return `rgba(44, 138, 124, ${alpha.toFixed(3)})`; // primary teal
  }
  const alpha = -v;
  return `rgba(220, 38, 38, ${alpha.toFixed(3)})`; // destructive red
}

export function CorrelationHeatmap({ data, isLoading }: CorrelationHeatmapProps) {
  const [hover, setHover] = useState<{ i: number; j: number; v: number } | null>(null);

  if (isLoading || !data) {
    return (
      <div className="h-[420px] flex items-center justify-center text-muted-foreground text-sm">
        <Loader2 className="h-5 w-5 animate-spin mr-2" />
        Loading correlation…
      </div>
    );
  }

  const n = data.features.length;
  const cell = 14;
  const labelWidth = 88;
  const labelHeight = 88;
  const size = n * cell;

  return (
    <div className="space-y-2">
      <div className="overflow-auto max-h-[480px] border rounded-md bg-card p-2">
        <svg
          width={size + labelWidth + 8}
          height={size + labelHeight + 8}
          role="img"
          aria-label="22x22 Pearson correlation matrix"
          className="block"
        >
          {/* Column labels (rotated) */}
          {data.features.map((f, i) => (
            <text
              key={`col-${f}`}
              x={labelWidth + i * cell + cell / 2}
              y={labelHeight - 4}
              fontSize={9}
              fill="hsl(var(--muted-foreground))"
              textAnchor="end"
              transform={`rotate(-60, ${labelWidth + i * cell + cell / 2}, ${labelHeight - 4})`}
            >
              {f}
            </text>
          ))}
          {/* Row labels */}
          {data.features.map((f, i) => (
            <text
              key={`row-${f}`}
              x={labelWidth - 4}
              y={labelHeight + i * cell + cell / 2 + 3}
              fontSize={9}
              fill="hsl(var(--muted-foreground))"
              textAnchor="end"
            >
              {f}
            </text>
          ))}
          {/* Cells */}
          {data.matrix.map((row, i) =>
            row.map((v, j) => (
              <rect
                key={`${i}-${j}`}
                x={labelWidth + j * cell}
                y={labelHeight + i * cell}
                width={cell}
                height={cell}
                fill={colorFor(v)}
                stroke={hover?.i === i && hover?.j === j ? "hsl(var(--ring))" : "hsl(var(--border))"}
                strokeWidth={hover?.i === i && hover?.j === j ? 1.5 : 0.5}
                onMouseEnter={() => setHover({ i, j, v })}
                onMouseLeave={() => setHover(null)}
              />
            )),
          )}
        </svg>
      </div>
      <div className="flex items-center justify-between text-xs">
        <div className="flex items-center gap-2">
          <span className="text-muted-foreground">−1</span>
          <div className="h-2 w-32 rounded-full bg-gradient-to-r from-destructive via-background to-primary" />
          <span className="text-muted-foreground">+1</span>
        </div>
        <div className="font-mono text-muted-foreground tabular-nums min-h-[1em]">
          {hover
            ? `${data.features[hover.i]} × ${data.features[hover.j]} = ${hover.v.toFixed(3)}`
            : "Hover a cell for details"}
        </div>
      </div>
    </div>
  );
}
