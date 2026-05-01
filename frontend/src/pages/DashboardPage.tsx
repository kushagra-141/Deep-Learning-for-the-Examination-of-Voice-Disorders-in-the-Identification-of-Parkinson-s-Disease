import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { motion } from "framer-motion";
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid,
  RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis,
  Legend, ReferenceLine, LineChart, Line
} from "recharts";
import { getModels, getRoc, getPr, getCalibration } from "../api/client";
import type { ModelInfo } from "../api/client";
import { qk } from "../api/queryKeys";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../components/ui/card";
import { Trophy, Target, Activity, TrendingUp, Loader2 } from "lucide-react";

const METRIC_COLORS = {
  accuracy:  "hsl(var(--primary))",
  precision: "hsl(142.1, 76.2%, 36.3%)",
  recall:    "hsl(38, 92%, 50%)",
  f1:        "hsl(262, 83%, 58%)",
};

const TAB_OPTIONS = ["Compare", "Radar", "CV Stability", "Curves"] as const;
type Tab = typeof TAB_OPTIONS[number];

function StatCard({ label, name, value, icon: Icon, color }: {
  label: string; name: string; value: string; icon: React.ElementType; color: string;
}) {
  return (
    <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }}>
      <Card className="hover:shadow-md transition-shadow">
        <CardHeader className="pb-2 flex flex-row items-center justify-between space-y-0">
          <CardDescription className="text-sm font-medium">{label}</CardDescription>
          <div className={`p-1.5 rounded-md ${color}`}>
            <Icon className="h-4 w-4" />
          </div>
        </CardHeader>
        <CardContent>
          <p className="text-xs text-muted-foreground uppercase tracking-wide mb-0.5 font-semibold capitalize">{name}</p>
          <div className="text-3xl font-black tabular-nums">{value}</div>
        </CardContent>
      </Card>
    </motion.div>
  );
}

// ── Curves tab ──────────────────────────────────────────────────────────────

function CurveCard({
  title,
  description,
  data,
  xKey,
  yKey,
  isLoading,
  diagonal = false,
}: {
  title: string;
  description: string;
  data: Array<Record<string, number>> | undefined;
  xKey: string;
  yKey: string;
  isLoading: boolean;
  diagonal?: boolean;
}) {
  return (
    <Card className="shadow-sm">
      <CardHeader className="pb-2">
        <CardTitle className="text-base">{title}</CardTitle>
        <CardDescription className="text-xs">{description}</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="h-[260px] w-full">
          {isLoading || !data ? (
            <div className="h-full flex items-center justify-center text-muted-foreground text-sm">
              <Loader2 className="h-5 w-5 animate-spin mr-2" />Loading…
            </div>
          ) : (
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={data} margin={{ top: 8, right: 8, left: 0, bottom: 8 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                <XAxis
                  dataKey={xKey}
                  type="number"
                  domain={[0, 1]}
                  tickFormatter={(v) => v.toFixed(1)}
                  tick={{ fontSize: 10, fill: "hsl(var(--muted-foreground))" }}
                  axisLine={false}
                  tickLine={false}
                />
                <YAxis
                  domain={[0, 1]}
                  tickFormatter={(v) => v.toFixed(1)}
                  tick={{ fontSize: 10, fill: "hsl(var(--muted-foreground))" }}
                  axisLine={false}
                  tickLine={false}
                />
                <Tooltip
                  content={({ active, payload }) => {
                    if (!active || !payload?.length) return null;
                    const p = payload[0]?.payload as Record<string, number> | undefined;
                    if (!p) return null;
                    return (
                      <div className="bg-background border border-border rounded-md p-2 shadow-md text-xs font-mono">
                        <div>{xKey}: {p[xKey]?.toFixed(3)}</div>
                        <div>{yKey}: {p[yKey]?.toFixed(3)}</div>
                      </div>
                    );
                  }}
                />
                {diagonal && (
                  <ReferenceLine
                    segment={[{ x: 0, y: 0 }, { x: 1, y: 1 }]}
                    stroke="hsl(var(--muted-foreground))"
                    strokeDasharray="4 4"
                  />
                )}
                <Line
                  type="monotone"
                  dataKey={yKey}
                  stroke="hsl(var(--primary))"
                  strokeWidth={2}
                  dot={false}
                  isAnimationActive={false}
                />
              </LineChart>
            </ResponsiveContainer>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

function CurvesTab({ models }: { models: ModelInfo[] }) {
  const [selected, setSelected] = useState<string>(
    models.find((m) => m.name === "lightgbm")?.name ?? models[0]?.name ?? "",
  );

  const roc = useQuery({
    queryKey: qk.modelRoc(selected),
    queryFn: () => getRoc(selected),
    enabled: !!selected,
  });
  const pr = useQuery({
    queryKey: qk.modelPr(selected),
    queryFn: () => getPr(selected),
    enabled: !!selected,
  });
  const cal = useQuery({
    queryKey: qk.modelCalibration(selected, 10),
    queryFn: () => getCalibration(selected, 10),
    enabled: !!selected,
  });

  const rocPoints = roc.data?.fpr.map((fpr, i) => ({ fpr, tpr: roc.data!.tpr[i]! }));
  const prPoints = pr.data?.recall.map((recall, i) => ({ recall, precision: pr.data!.precision[i]! }));
  const calPoints = cal.data?.mean_predicted_probability.map((mean_pred, i) => ({
    mean_pred,
    fraction: cal.data!.fraction_of_positives[i]!,
  }));

  return (
    <div className="space-y-4">
      <Card className="shadow-sm">
        <CardHeader className="pb-3">
          <div className="flex flex-wrap items-center gap-3 justify-between">
            <div>
              <CardTitle>Detail Curves</CardTitle>
              <CardDescription className="text-xs">
                Pick a model — ROC, precision/recall, and calibration are computed on the held-out test split.
              </CardDescription>
            </div>
            <select
              value={selected}
              onChange={(e) => setSelected(e.target.value)}
              className="text-sm bg-background border border-input rounded-md px-3 py-1.5 capitalize font-medium"
              aria-label="Select model"
            >
              {models.map((m) => (
                <option key={m.name} value={m.name}>
                  {m.name.replace(/_/g, " ")}
                </option>
              ))}
            </select>
          </div>
        </CardHeader>
      </Card>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <CurveCard
          title="ROC"
          description="True positive rate vs. false positive rate. Higher curve = better separation."
          data={rocPoints}
          xKey="fpr"
          yKey="tpr"
          isLoading={roc.isLoading}
          diagonal
        />
        <CurveCard
          title="Precision–Recall"
          description="Precision vs. recall across thresholds. Higher curve = fewer false positives at high recall."
          data={prPoints}
          xKey="recall"
          yKey="precision"
          isLoading={pr.isLoading}
        />
        <CurveCard
          title="Reliability (Calibration)"
          description="Predicted probability vs. observed fraction of positives. Closer to diagonal = better calibrated."
          data={calPoints}
          xKey="mean_pred"
          yKey="fraction"
          isLoading={cal.isLoading}
          diagonal
        />
      </div>
    </div>
  );
}

// Custom tooltip for Recharts
function CustomTooltip({ active, payload, label }: any) {
  if (!active || !payload?.length) return null;
  return (
    <div className="bg-background border border-border rounded-lg p-3 shadow-xl text-sm">
      <p className="font-semibold mb-2 capitalize">{label}</p>
      {payload.map((p: any) => (
        <div key={p.name} className="flex items-center gap-2">
          <div className="h-2.5 w-2.5 rounded-full" style={{ backgroundColor: p.fill ?? p.color }} />
          <span className="text-muted-foreground capitalize">{p.name}:</span>
          <span className="font-mono font-bold">{typeof p.value === "number" ? `${p.value.toFixed(1)}%` : p.value}</span>
        </div>
      ))}
    </div>
  );
}

export default function DashboardPage() {
  const [activeTab, setActiveTab] = useState<Tab>("Compare");

  const { data: models, isLoading, error } = useQuery({
    queryKey: ["models"],
    queryFn: getModels,
  });

  if (isLoading) {
    return (
      <div className="container py-12 flex justify-center items-center min-h-[50vh]">
        <div className="flex flex-col items-center gap-4">
          <div className="h-10 w-10 border-4 border-primary/20 border-t-primary rounded-full animate-spin" />
          <p className="text-muted-foreground font-medium">Loading analytics...</p>
        </div>
      </div>
    );
  }

  if (error || !models || models.length === 0) {
    return (
      <div className="container py-12">
        <Card className="border-destructive/50 bg-destructive/5">
          <CardHeader>
            <CardTitle className="text-destructive">Failed to load analytics</CardTitle>
            <CardDescription>
              {error?.message ?? "No model data available. Run the training script."}
            </CardDescription>
          </CardHeader>
        </Card>
      </div>
    );
  }

  // Prepare chart data
  const chartData = models.map((m: ModelInfo) => ({
    name: m.name.replace(/_/g, " "),
    accuracy:  Number(((m.metrics.accuracy  ?? 0) * 100).toFixed(1)),
    precision: Number(((m.metrics.precision ?? 0) * 100).toFixed(1)),
    recall:    Number(((m.metrics.recall    ?? 0) * 100).toFixed(1)),
    f1:        Number(((m.metrics.f1        ?? 0) * 100).toFixed(1)),
    cv_mean:   Number(((m.metrics.cv_accuracy_mean ?? 0) * 100).toFixed(1)),
    cv_std:    Number(((m.metrics.cv_accuracy_std  ?? 0) * 100).toFixed(2)),
  })).sort((a, b) => b.accuracy - a.accuracy);

  const best = chartData[0];
  const bestPrecision = [...chartData].sort((a, b) => b.precision - a.precision)[0];
  const bestRecall    = [...chartData].sort((a, b) => b.recall    - a.recall   )[0];
  const bestF1        = [...chartData].sort((a, b) => b.f1        - a.f1       )[0];

  if (!best || !bestPrecision || !bestRecall || !bestF1) return null;

  // Radar data — one model per spoke, value = F1
  const radarData = [
    { metric: "Accuracy",  ...Object.fromEntries(chartData.map(m => [m.name, m.accuracy]))  },
    { metric: "Precision", ...Object.fromEntries(chartData.map(m => [m.name, m.precision])) },
    { metric: "Recall",    ...Object.fromEntries(chartData.map(m => [m.name, m.recall]))    },
    { metric: "F1",        ...Object.fromEntries(chartData.map(m => [m.name, m.f1]))        },
  ];

  return (
    <div className="container py-10 max-w-6xl mx-auto space-y-8">
      {/* Header */}
      <motion.div
        className="space-y-2"
        initial={{ opacity: 0, y: -12 }}
        animate={{ opacity: 1, y: 0 }}
      >
        <h1 className="text-3xl font-bold tracking-tight">Ensemble Analytics</h1>
        <p className="text-muted-foreground">
          Live performance metrics for {models.length} classifiers trained on the Oxford Parkinson's dataset.
        </p>
      </motion.div>

      {/* Stat Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <StatCard label="Best Accuracy"  name={best.name}          value={`${best.accuracy}%`}          icon={Trophy}     color="bg-primary/10 text-primary" />
        <StatCard label="Best Precision" name={bestPrecision.name} value={`${bestPrecision.precision}%`} icon={Target}     color="bg-success/10 text-success" />
        <StatCard label="Best Recall"    name={bestRecall.name}    value={`${bestRecall.recall}%`}        icon={Activity}   color="bg-warning/10 text-warning" />
        <StatCard label="Best F1"        name={bestF1.name}        value={`${bestF1.f1}%`}                icon={TrendingUp} color="bg-violet-500/10 text-violet-500" />
      </div>

      {/* Tabs */}
      <div className="flex gap-1 p-1 bg-muted rounded-lg w-fit">
        {TAB_OPTIONS.map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`relative px-4 py-1.5 text-sm font-medium rounded-md transition-colors ${
              activeTab === tab ? "bg-background text-foreground shadow-sm" : "text-muted-foreground hover:text-foreground"
            }`}
          >
            {tab}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      <motion.div
        key={activeTab}
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.25 }}
      >
        {activeTab === "Compare" && (
          <Card className="shadow-sm">
            <CardHeader>
              <CardTitle>Metric Comparison</CardTitle>
              <CardDescription>Accuracy, Precision, Recall, and F1 across all models — sorted by accuracy.</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="h-[420px] w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={chartData} margin={{ top: 20, right: 20, left: 0, bottom: 24 }} barGap={2} barCategoryGap="28%">
                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="hsl(var(--border))" />
                    <XAxis dataKey="name" axisLine={false} tickLine={false} tick={{ fontSize: 11, fill: "hsl(var(--muted-foreground))" }} dy={10} />
                    <YAxis domain={[50, 100]} axisLine={false} tickLine={false} tick={{ fontSize: 11, fill: "hsl(var(--muted-foreground))" }} tickFormatter={v => `${v}%`} />
                    <Tooltip content={<CustomTooltip />} cursor={{ fill: "hsl(var(--accent))", opacity: 0.3 }} />
                    <Legend wrapperStyle={{ paddingTop: "16px", fontSize: "12px" }} />
                    <Bar dataKey="accuracy"  name="Accuracy"  fill={METRIC_COLORS.accuracy}  radius={[4, 4, 0, 0]} />
                    <Bar dataKey="precision" name="Precision" fill={METRIC_COLORS.precision} radius={[4, 4, 0, 0]} />
                    <Bar dataKey="recall"    name="Recall"    fill={METRIC_COLORS.recall}    radius={[4, 4, 0, 0]} />
                    <Bar dataKey="f1"        name="F1 Score"  fill={METRIC_COLORS.f1}        radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </CardContent>
          </Card>
        )}

        {activeTab === "Radar" && (
          <Card className="shadow-sm">
            <CardHeader>
              <CardTitle>Metric Profile Radar</CardTitle>
              <CardDescription>Each spoke represents a different performance metric. Larger area = stronger overall model.</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="h-[420px] w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <RadarChart data={radarData}>
                    <PolarGrid stroke="hsl(var(--border))" />
                    <PolarAngleAxis dataKey="metric" tick={{ fontSize: 13, fill: "hsl(var(--foreground))", fontWeight: 600 }} />
                    <PolarRadiusAxis domain={[50, 100]} tick={{ fontSize: 10, fill: "hsl(var(--muted-foreground))" }} tickFormatter={v => `${v}%`} />
                    {chartData.slice(0, 5).map((m, i) => {
                      const hues = [200, 142, 38, 262, 0];
                      return (
                        <Radar key={m.name} name={m.name} dataKey={m.name}
                          stroke={`hsl(${hues[i]}, 70%, 50%)`} fill={`hsl(${hues[i]}, 70%, 50%)`} fillOpacity={0.12} strokeWidth={2} />
                      );
                    })}
                    <Legend wrapperStyle={{ fontSize: "12px" }} />
                    <Tooltip content={<CustomTooltip />} />
                  </RadarChart>
                </ResponsiveContainer>
              </div>
              <p className="text-xs text-muted-foreground mt-2 text-center">Showing top 5 models by accuracy</p>
            </CardContent>
          </Card>
        )}

        {activeTab === "Curves" && <CurvesTab models={models} />}

        {activeTab === "CV Stability" && (
          <Card className="shadow-sm">
            <CardHeader>
              <CardTitle>Cross-Validation Stability</CardTitle>
              <CardDescription>Mean CV accuracy and ± std deviation from 5-fold cross-validation.</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="h-[380px] w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={chartData.sort((a, b) => b.cv_mean - a.cv_mean)} margin={{ top: 20, right: 20, left: 0, bottom: 24 }}>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="hsl(var(--border))" />
                    <XAxis dataKey="name" axisLine={false} tickLine={false} tick={{ fontSize: 11, fill: "hsl(var(--muted-foreground))" }} dy={10} />
                    <YAxis domain={[50, 100]} axisLine={false} tickLine={false} tick={{ fontSize: 11, fill: "hsl(var(--muted-foreground))" }} tickFormatter={v => `${v}%`} />
                    <ReferenceLine y={80} stroke="hsl(var(--primary))" strokeDasharray="4 4" label={{ value: "80% baseline", position: "insideRight", fontSize: 11, fill: "hsl(var(--primary))" }} />
                    <Tooltip content={<CustomTooltip />} cursor={{ fill: "hsl(var(--accent))", opacity: 0.3 }} />
                    <Bar dataKey="cv_mean" name="CV Mean" fill="hsl(var(--primary))" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
              {/* CV Table */}
              <div className="mt-6 overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="text-xs text-muted-foreground uppercase border-b">
                      <th className="pb-2 text-left font-medium">Model</th>
                      <th className="pb-2 text-right font-medium">Accuracy</th>
                      <th className="pb-2 text-right font-medium">Precision</th>
                      <th className="pb-2 text-right font-medium">Recall</th>
                      <th className="pb-2 text-right font-medium">F1</th>
                      <th className="pb-2 text-right font-medium">CV Mean ± Std</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-border">
                    {chartData.sort((a, b) => b.accuracy - a.accuracy).map((m, i) => (
                      <tr key={m.name} className="hover:bg-muted/30 transition-colors">
                        <td className="py-2.5">
                          <div className="flex items-center gap-2">
                            {i === 0 && <span className="text-amber-500">🏆</span>}
                            <span className="font-medium capitalize">{m.name}</span>
                          </div>
                        </td>
                        <td className="py-2.5 text-right font-mono text-xs">{m.accuracy}%</td>
                        <td className="py-2.5 text-right font-mono text-xs">{m.precision}%</td>
                        <td className="py-2.5 text-right font-mono text-xs">{m.recall}%</td>
                        <td className="py-2.5 text-right font-mono text-xs">{m.f1}%</td>
                        <td className="py-2.5 text-right font-mono text-xs">
                          {m.cv_mean}% <span className="text-muted-foreground">±{m.cv_std}</span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>
        )}
      </motion.div>
    </div>
  );
}
