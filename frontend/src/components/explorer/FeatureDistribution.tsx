import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { Loader2 } from "lucide-react";
import type { FeatureDistribution as FeatureDistributionType } from "../../api/client";

interface FeatureDistributionProps {
  data: FeatureDistributionType | undefined;
  isLoading: boolean;
}

export function FeatureDistribution({ data, isLoading }: FeatureDistributionProps) {
  if (isLoading || !data) {
    return (
      <div className="h-[260px] flex items-center justify-center text-muted-foreground text-sm">
        <Loader2 className="h-5 w-5 animate-spin mr-2" />
        Loading distribution…
      </div>
    );
  }

  // The endpoint returns a single histogram (`bins` + `counts`) plus per-class
  // box stats. To show class-separated bars we'd need backend changes; for now,
  // overlay the overall histogram and surface per-class summary stats below.
  const series = data.bins.slice(0, -1).map((edge, i) => ({
    bin: ((edge + (data.bins[i + 1] ?? edge)) / 2).toFixed(3),
    count: data.counts[i] ?? 0,
  }));

  const healthy = data.by_class.healthy;
  const parkinsons = data.by_class.parkinsons;

  return (
    <div className="space-y-3">
      <div className="h-[240px] w-full">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={series} margin={{ top: 8, right: 8, left: 0, bottom: 8 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
            <XAxis
              dataKey="bin"
              tick={{ fontSize: 9, fill: "hsl(var(--muted-foreground))" }}
              axisLine={false}
              tickLine={false}
              interval="preserveStartEnd"
            />
            <YAxis
              tick={{ fontSize: 10, fill: "hsl(var(--muted-foreground))" }}
              axisLine={false}
              tickLine={false}
            />
            <Tooltip
              content={({ active, payload, label }) => {
                if (!active || !payload?.length) return null;
                return (
                  <div className="bg-background border rounded-md p-2 shadow-md text-xs font-mono">
                    <div>bin: {label}</div>
                    <div>count: {payload[0]?.value as number}</div>
                  </div>
                );
              }}
            />
            <Legend wrapperStyle={{ fontSize: 11 }} />
            <Bar dataKey="count" name="All rows" fill="hsl(var(--primary))" />
          </BarChart>
        </ResponsiveContainer>
      </div>
      <div className="grid grid-cols-2 gap-3 text-xs">
        <div className="rounded-md border bg-card p-2 space-y-0.5">
          <div className="font-semibold text-success uppercase tracking-wider text-[10px]">
            Healthy
          </div>
          <div className="font-mono tabular-nums text-muted-foreground">
            mean: {healthy.mean.toFixed(4)}
          </div>
          <div className="font-mono tabular-nums text-muted-foreground">
            median: {healthy.median.toFixed(4)}
          </div>
          <div className="font-mono tabular-nums text-muted-foreground">
            σ: {healthy.std.toFixed(4)}
          </div>
        </div>
        <div className="rounded-md border bg-card p-2 space-y-0.5">
          <div className="font-semibold text-destructive uppercase tracking-wider text-[10px]">
            Parkinson's
          </div>
          <div className="font-mono tabular-nums text-muted-foreground">
            mean: {parkinsons.mean.toFixed(4)}
          </div>
          <div className="font-mono tabular-nums text-muted-foreground">
            median: {parkinsons.median.toFixed(4)}
          </div>
          <div className="font-mono tabular-nums text-muted-foreground">
            σ: {parkinsons.std.toFixed(4)}
          </div>
        </div>
      </div>
    </div>
  );
}
