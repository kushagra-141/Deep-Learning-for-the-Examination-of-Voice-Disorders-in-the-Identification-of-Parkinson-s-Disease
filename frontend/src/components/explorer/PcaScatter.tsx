import { useMemo } from "react";
import {
  CartesianGrid,
  Legend,
  ReferenceArea,
  ResponsiveContainer,
  Scatter,
  ScatterChart,
  Tooltip,
  XAxis,
  YAxis,
  ZAxis,
} from "recharts";
import { Loader2 } from "lucide-react";
import type { PCAProjection } from "../../api/client";

export interface BrushRect {
  x0: number;
  y0: number;
  x1: number;
  y1: number;
}

interface PcaScatterProps {
  data: PCAProjection | undefined;
  isLoading: boolean;
  brush: BrushRect | null;
  onBrushChange: (rect: BrushRect | null) => void;
}

export function PcaScatter({ data, isLoading, brush, onBrushChange }: PcaScatterProps) {
  const partitioned = useMemo(() => {
    if (!data) return { healthy: [], parkinsons: [] };
    const healthy = data.points.filter((p) => p.label === 0);
    const parkinsons = data.points.filter((p) => p.label === 1);
    return { healthy, parkinsons };
  }, [data]);

  if (isLoading || !data) {
    return (
      <div className="h-[360px] flex items-center justify-center text-muted-foreground text-sm">
        <Loader2 className="h-5 w-5 animate-spin mr-2" />
        Computing PCA…
      </div>
    );
  }

  const xVals = data.points.map((p) => p.x);
  const yVals = data.points.map((p) => p.y);
  const xPad = (Math.max(...xVals) - Math.min(...xVals)) * 0.05 || 0.1;
  const yPad = (Math.max(...yVals) - Math.min(...yVals)) * 0.05 || 0.1;
  const xDomain: [number, number] = [Math.min(...xVals) - xPad, Math.max(...xVals) + xPad];
  const yDomain: [number, number] = [Math.min(...yVals) - yPad, Math.max(...yVals) + yPad];
  const ev1 = data.explained_variance[0] ?? 0;
  const ev2 = data.explained_variance[1] ?? 0;

  // Brush gesture state lives in the parent — we just track drag start here.
  let dragStart: { x: number; y: number } | null = null;

  return (
    <div className="space-y-2">
      <div className="h-[360px] w-full">
        <ResponsiveContainer width="100%" height="100%">
          <ScatterChart
            margin={{ top: 12, right: 12, left: 0, bottom: 12 }}
            onMouseDown={(e) => {
              if (e?.xValue !== undefined && e?.yValue !== undefined) {
                dragStart = { x: e.xValue as number, y: e.yValue as number };
              }
            }}
            onMouseMove={(e) => {
              if (dragStart && e?.xValue !== undefined && e?.yValue !== undefined) {
                onBrushChange({
                  x0: Math.min(dragStart.x, e.xValue as number),
                  y0: Math.min(dragStart.y, e.yValue as number),
                  x1: Math.max(dragStart.x, e.xValue as number),
                  y1: Math.max(dragStart.y, e.yValue as number),
                });
              }
            }}
            onMouseUp={() => {
              dragStart = null;
            }}
          >
            <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
            <XAxis
              type="number"
              dataKey="x"
              domain={xDomain}
              name={`PC1 (${(ev1 * 100).toFixed(1)}%)`}
              tick={{ fontSize: 10, fill: "hsl(var(--muted-foreground))" }}
              tickFormatter={(v: number) => v.toFixed(1)}
              axisLine={false}
              tickLine={false}
            />
            <YAxis
              type="number"
              dataKey="y"
              domain={yDomain}
              name={`PC2 (${(ev2 * 100).toFixed(1)}%)`}
              tick={{ fontSize: 10, fill: "hsl(var(--muted-foreground))" }}
              tickFormatter={(v: number) => v.toFixed(1)}
              axisLine={false}
              tickLine={false}
            />
            <ZAxis range={[40, 40]} />
            <Tooltip
              cursor={{ strokeDasharray: "3 3" }}
              content={({ active, payload }) => {
                if (!active || !payload?.length) return null;
                const p = payload[0]?.payload as { x: number; y: number; label: number } | undefined;
                if (!p) return null;
                return (
                  <div className="bg-background border rounded-md p-2 shadow-md text-xs font-mono">
                    <div>PC1: {p.x.toFixed(3)}</div>
                    <div>PC2: {p.y.toFixed(3)}</div>
                    <div>class: {p.label === 1 ? "Parkinson's" : "Healthy"}</div>
                  </div>
                );
              }}
            />
            <Legend wrapperStyle={{ fontSize: 11 }} />
            <Scatter
              name="Healthy"
              data={partitioned.healthy}
              fill="hsl(var(--success))"
              fillOpacity={0.65}
            />
            <Scatter
              name="Parkinson's"
              data={partitioned.parkinsons}
              fill="hsl(var(--destructive))"
              fillOpacity={0.65}
            />
            {brush && (
              <ReferenceArea
                x1={brush.x0}
                x2={brush.x1}
                y1={brush.y0}
                y2={brush.y1}
                fill="hsl(var(--primary))"
                fillOpacity={0.1}
                stroke="hsl(var(--primary))"
                strokeOpacity={0.5}
              />
            )}
          </ScatterChart>
        </ResponsiveContainer>
      </div>
      <p className="text-[10px] text-muted-foreground text-center">
        Click and drag on the plot to brush a region — points inside will filter the dataset table below.
      </p>
    </div>
  );
}
