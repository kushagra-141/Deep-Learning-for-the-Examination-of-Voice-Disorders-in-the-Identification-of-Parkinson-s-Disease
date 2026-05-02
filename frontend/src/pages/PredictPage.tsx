import { useForm } from "react-hook-form";
import { motion, AnimatePresence } from "framer-motion";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { useEffect, useRef, useState } from "react";
import { Loader2, Zap, FlaskConical, BarChart2, ChevronRight, AlertTriangle, SlidersHorizontal, MessageSquare } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { Badge } from "../components/ui/badge";
import { usePrediction } from "../hooks/usePrediction";
import { WhatIfDrawer } from "../components/prediction/WhatIfDrawer";
import { LLMExplanation } from "../components/prediction/LLMExplanation";
import { ShapWaterfall } from "../components/prediction/ShapWaterfall";
import { ShareLinkButton } from "../components/prediction/ShareLinkButton";
import { DownloadReportButton } from "../components/prediction/DownloadReportButton";
import { RecentList } from "../components/common/RecentList";
import { ChatSidebar } from "../components/llm/ChatSidebar";
import { getPredictSample } from "../api/client";
import { readShareFromLocation } from "../lib/share";
import { useRecentPredictions, riskFromProbability } from "../stores/recent";

const FEATURE_GROUPS = [
  {
    title: "Frequency",
    icon: "〜",
    color: "text-blue-500",
    features: ["MDVP:Fo(Hz)", "MDVP:Fhi(Hz)", "MDVP:Flo(Hz)"],
  },
  {
    title: "Jitter",
    icon: "⟿",
    color: "text-violet-500",
    features: ["MDVP:Jitter(%)", "MDVP:Jitter(Abs)", "MDVP:RAP", "MDVP:PPQ", "Jitter:DDP"],
  },
  {
    title: "Shimmer",
    icon: "◈",
    color: "text-orange-500",
    features: ["MDVP:Shimmer", "MDVP:Shimmer(dB)", "Shimmer:APQ3", "Shimmer:APQ5", "MDVP:APQ", "Shimmer:DDA"],
  },
  {
    title: "Harmonicity & Nonlinear",
    icon: "∿",
    color: "text-teal-500",
    features: ["NHR", "HNR", "RPDE", "DFA", "spread1", "spread2", "D2", "PPE"],
  }
];

// Fallback sample used only when the /predict/sample endpoint is unreachable.
const SAMPLE_DATA: Record<string, number> = {
  "MDVP:Fo(Hz)": 154.23, "MDVP:Fhi(Hz)": 197.10, "MDVP:Flo(Hz)": 116.32,
  "MDVP:Jitter(%)": 0.0067, "MDVP:Jitter(Abs)": 0.00004, "MDVP:RAP": 0.0034,
  "MDVP:PPQ": 0.0038, "Jitter:DDP": 0.0102,
  "MDVP:Shimmer": 0.029, "MDVP:Shimmer(dB)": 0.282, "Shimmer:APQ3": 0.0145,
  "Shimmer:APQ5": 0.0179, "MDVP:APQ": 0.024, "Shimmer:DDA": 0.0436,
  "NHR": 0.0162, "HNR": 22.4,
  "RPDE": 0.4985, "DFA": 0.7180, "spread1": -5.94, "spread2": 0.226, "D2": 2.31, "PPE": 0.207
};

function getRiskLevel(prob: number) {
  if (prob >= 0.7) return { label: "High Risk", color: "destructive", barColor: "bg-destructive", textColor: "text-destructive", bg: "bg-destructive/5" };
  if (prob >= 0.4) return { label: "Borderline", color: "warning", barColor: "bg-warning", textColor: "text-warning", bg: "bg-warning/5" };
  return { label: "Low Risk", color: "success", barColor: "bg-success", textColor: "text-success", bg: "bg-success/5" };
}

export default function PredictPage() {
  const { mutate: predict, isPending, data, error, reset: resetMutation } = usePrediction();
  const { register, handleSubmit, reset, getValues } = useForm<Record<string, number>>();
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [chatOpen, setChatOpen] = useState(false);
  const [lastSubmitted, setLastSubmitted] = useState<Record<string, number>>({});
  const [sampleLoading, setSampleLoading] = useState(false);
  const [sampleError, setSampleError] = useState<string | null>(null);
  const addRecent = useRecentPredictions((s) => s.add);
  const location = useLocation();
  const navigate = useNavigate();
  const sharePrefillApplied = useRef(false);

  // Share-link prefill: ?q=<encoded> populates the form; ?auto=1 also re-submits.
  useEffect(() => {
    if (sharePrefillApplied.current) return;
    const incoming = readShareFromLocation(location.search);
    if (!incoming) return;
    sharePrefillApplied.current = true;
    reset(incoming.payload.features);
    if (incoming.autoSubmit) {
      predict(incoming.payload.features);
      setLastSubmitted(incoming.payload.features);
    }
    // Strip query so a refresh doesn't re-submit forever.
    navigate("/predict", { replace: true });
  }, [location.search, navigate, predict, reset]);

  // Persist successful predictions to the recent-list store.
  useEffect(() => {
    if (!data) return;
    addRecent({
      predictionId: data.prediction_id,
      createdAt: data.created_at,
      probability: data.ensemble.probability,
      riskLabel: riskFromProbability(data.ensemble.probability),
      inputMode: "manual",
      features: lastSubmitted,
      primaryModel: data.primary_model,
    });
    // Only fire once per new prediction_id.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [data?.prediction_id]);

  const onSubmit = (formData: Record<string, number>) => {
    const numericFeatures: Record<string, number> = {};
    for (const key in formData) {
      numericFeatures[key] = parseFloat(String(formData[key])) || 0.0;
    }
    setLastSubmitted(numericFeatures);
    predict(numericFeatures);
  };

  const handleRestoreRecent = (entry: { features: Record<string, number> }) => {
    reset(entry.features);
    resetMutation();
    setLastSubmitted({});
  };

  // Suppress unused warning while still typing this for future use.
  void getValues;

  // Cmd/Ctrl+K opens the chat sidebar when a result is available.
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === "k" && data) {
        e.preventDefault();
        setChatOpen(true);
      }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [data]);

  const loadSample = async () => {
    setSampleLoading(true);
    setSampleError(null);
    try {
      const sample = await getPredictSample("random");
      reset(sample);
      resetMutation();
    } catch (e) {
      // Backend unreachable — fall back to a hardcoded row so the form still
      // populates and the user can see the prediction flow.
      reset(SAMPLE_DATA);
      resetMutation();
      setSampleError(e instanceof Error ? e.message : "Could not load a fresh sample");
    } finally {
      setSampleLoading(false);
    }
  };

  const handleApplyFromDrawer = (values: Record<string, number>) => {
    reset(values);
  };

  const risk = data ? getRiskLevel(data.ensemble.probability) : null;

  return (
    <div className="container py-8 max-w-7xl mx-auto">
      <div className="flex flex-col gap-2 mb-8">
        <div className="flex items-center gap-2">
          <Badge variant="outline" className="text-xs"><FlaskConical className="h-3 w-3 mr-1" />Manual Analysis</Badge>
          <Link to="/audio">
            <Badge variant="outline" className="text-xs cursor-pointer hover:bg-accent transition-colors">
              <Zap className="h-3 w-3 mr-1 text-primary" />Try Live Audio <ChevronRight className="h-3 w-3 ml-1" />
            </Badge>
          </Link>
        </div>
        <h1 className="text-3xl font-bold tracking-tight">Feature Prediction</h1>
        <p className="text-muted-foreground">
          Enter the 22 acoustic voice features to run a real-time ensemble prediction across 8 classifiers.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-5 gap-8 items-start">
        {/* Form — 3 columns */}
        <div className="lg:col-span-3">
          <Card className="shadow-md">
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle>Feature Inputs</CardTitle>
                  <CardDescription>22 acoustic dimensions from MDVP voice analysis.</CardDescription>
                </div>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={loadSample}
                  className="shrink-0"
                  disabled={sampleLoading}
                  aria-label="Load a random sample from the dataset"
                >
                  {sampleLoading ? (
                    <><Loader2 className="mr-2 h-3 w-3 animate-spin" />Loading…</>
                  ) : (
                    "Load Sample"
                  )}
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleSubmit(onSubmit)} className="space-y-8">
                {FEATURE_GROUPS.map((group) => (
                  <div key={group.title} className="space-y-3">
                    <h3 className={`font-semibold text-sm uppercase tracking-wider flex items-center gap-2 ${group.color}`}>
                      <span>{group.icon}</span> {group.title}
                    </h3>
                    <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
                      {group.features.map((feat) => (
                        <div key={feat} className="space-y-1">
                          <Label htmlFor={feat} className="text-xs text-muted-foreground font-mono">{feat}</Label>
                          <Input
                            id={feat}
                            type="number"
                            step="any"
                            placeholder="0.0"
                            className="font-mono text-sm h-9"
                            {...register(feat, { required: true })}
                          />
                        </div>
                      ))}
                    </div>
                  </div>
                ))}

                <div className="pt-4 border-t flex gap-3">
                  <Button type="submit" className="flex-1 h-12 text-base font-semibold" disabled={isPending}>
                    {isPending ? (
                      <><Loader2 className="mr-2 h-5 w-5 animate-spin" />Analyzing Ensemble...</>
                    ) : (
                      <><BarChart2 className="mr-2 h-5 w-5" />Run Prediction</>
                    )}
                  </Button>
                </div>
                {error && (
                  <p className="text-destructive text-sm text-center flex items-center justify-center gap-2">
                    <AlertTriangle className="h-4 w-4" />{error.message}
                  </p>
                )}
                {sampleError && !error && (
                  <p className="text-warning text-xs text-center flex items-center justify-center gap-2">
                    <AlertTriangle className="h-3 w-3" />Sample API unreachable — using offline fallback ({sampleError})
                  </p>
                )}
              </form>
            </CardContent>
          </Card>
        </div>

        {/* Results — 2 columns, sticky */}
        <div className="lg:col-span-2 lg:sticky lg:top-24 space-y-4">
          <AnimatePresence mode="wait">
            {!data && !isPending ? (
              <motion.div
                key="empty"
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -8 }}
              >
                <Card className="border-dashed min-h-[340px] flex flex-col items-center justify-center text-center text-muted-foreground p-8 space-y-4">
                  <BarChart2 className="h-12 w-12 opacity-20" />
                  <div>
                    <p className="font-medium">Ensemble result will appear here</p>
                    <p className="text-sm mt-1">Load sample data or enter feature values, then run prediction.</p>
                  </div>
                </Card>
              </motion.div>
            ) : isPending ? (
              <motion.div key="loading" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
                <Card className="min-h-[340px] flex flex-col items-center justify-center space-y-4">
                  <div className="relative">
                    <div className="h-16 w-16 rounded-full border-4 border-primary/20 border-t-primary animate-spin" />
                    <div className="absolute inset-0 flex items-center justify-center">
                      <div className="h-8 w-8 rounded-full bg-primary/10 animate-pulse" />
                    </div>
                  </div>
                  <div className="text-center">
                    <p className="font-semibold">Running 8 classifiers...</p>
                    <p className="text-sm text-muted-foreground mt-1">Computing soft-vote ensemble</p>
                  </div>
                </Card>
              </motion.div>
            ) : data && risk ? (
              <motion.div
                key="result"
                initial={{ opacity: 0, scale: 0.97 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0 }}
                transition={{ duration: 0.3 }}
                className="space-y-4"
              >
                {/* Main Result Card */}
                <Card className={`overflow-hidden border-2 ${risk.bg}`}>
                  <div className={`h-2 w-full ${risk.barColor}`} />
                  <CardContent className="p-6 text-center space-y-4">
                    <Badge className={`text-xs uppercase tracking-widest px-3 py-1 ${risk.bg} ${risk.textColor} border-current`}>
                      {risk.label}
                    </Badge>
                    <div>
                      <motion.div
                        className={`text-6xl font-black tabular-nums ${risk.textColor}`}
                        initial={{ scale: 0.5, opacity: 0 }}
                        animate={{ scale: 1, opacity: 1 }}
                        transition={{ type: "spring", stiffness: 200, damping: 15, delay: 0.15 }}
                      >
                        {(data.ensemble.probability * 100).toFixed(1)}%
                      </motion.div>
                      <p className="text-muted-foreground text-sm mt-1">Ensemble probability of Parkinson's</p>
                    </div>

                    {/* Animated progress bar */}
                    <div className="w-full bg-muted rounded-full h-2 overflow-hidden">
                      <motion.div
                        className={`h-full rounded-full ${risk.barColor}`}
                        initial={{ width: 0 }}
                        animate={{ width: `${data.ensemble.probability * 100}%` }}
                        transition={{ duration: 0.8, ease: "easeOut", delay: 0.2 }}
                      />
                    </div>
                  </CardContent>
                </Card>

                {/* SHAP waterfall — top contributors with toggle to show all 22 */}
                {data.ensemble.shap_top && data.ensemble.shap_top.length > 0 && (
                  <ShapWaterfall
                    contributions={data.ensemble.shap_top}
                    primaryModel={data.primary_model}
                  />
                )}

                {/* Per-model breakdown */}
                <Card>
                  <CardHeader className="pb-2">
                    <CardTitle className="text-sm font-semibold uppercase tracking-wider text-muted-foreground">
                      Model Breakdown ({data.per_model.length} classifiers)
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-2">
                    {data.per_model.map((m, i) => {
                      const p = m.probability;
                      const modelRisk = getRiskLevel(p);
                      return (
                        <motion.div
                          key={m.model_name}
                          initial={{ opacity: 0, x: -12 }}
                          animate={{ opacity: 1, x: 0 }}
                          transition={{ delay: i * 0.05 }}
                          className="flex items-center gap-3"
                        >
                          <span className="text-xs font-mono text-muted-foreground w-28 shrink-0 capitalize">
                            {m.model_name.replace(/_/g, " ")}
                          </span>
                          <div className="flex-1 bg-muted rounded-full h-1.5 overflow-hidden">
                            <motion.div
                              className={`h-full rounded-full ${modelRisk.barColor}`}
                              initial={{ width: 0 }}
                              animate={{ width: `${p * 100}%` }}
                              transition={{ duration: 0.6, ease: "easeOut", delay: 0.1 + i * 0.05 }}
                            />
                          </div>
                          <span className={`text-xs font-mono font-bold w-12 text-right ${modelRisk.textColor}`}>
                            {(p * 100).toFixed(0)}%
                          </span>
                        </motion.div>
                      );
                    })}
                  </CardContent>
                </Card>

                {/* Disclaimer */}
                <p className="text-[10px] text-muted-foreground text-center leading-relaxed px-2">
                  {data.disclaimer}
                </p>

                {/* What-If trigger */}
                <Button
                  variant="outline"
                  className="w-full border-dashed"
                  onClick={() => setDrawerOpen(true)}
                >
                  <SlidersHorizontal className="h-4 w-4 mr-2 text-primary" />
                  Explore What-If Scenarios
                </Button>

                {/* Chat / Share / Download row */}
                <Button
                  variant="outline"
                  className="w-full"
                  onClick={() => setChatOpen(true)}
                >
                  <MessageSquare className="h-4 w-4 mr-2 text-primary" />
                  Discuss this result
                  <span className="ml-auto text-[10px] font-mono text-muted-foreground">⌘K</span>
                </Button>
                <div className="grid grid-cols-2 gap-2">
                  <ShareLinkButton
                    features={lastSubmitted}
                    probability={data.ensemble.probability}
                  />
                  <DownloadReportButton
                    prediction={data}
                    features={lastSubmitted}
                  />
                </div>

                <LLMExplanation
                  features={lastSubmitted}
                  probability={data.ensemble.probability}
                  inputMode="manual"
                />
              </motion.div>
            ) : null}
          </AnimatePresence>

          {/* Recent predictions — always visible below the result column */}
          <RecentList onRestore={handleRestoreRecent} />
        </div>
      </div>

      {/* What-If Drawer */}
      <AnimatePresence>
        {drawerOpen && (
          <WhatIfDrawer
            open={drawerOpen}
            onOpenChange={setDrawerOpen}
            baseline={lastSubmitted}
            onApply={handleApplyFromDrawer}
          />
        )}
      </AnimatePresence>

      {/* Chat Sidebar */}
      <AnimatePresence>
        {chatOpen && data && (
          <ChatSidebar
            open={chatOpen}
            onOpenChange={setChatOpen}
            prediction={data}
          />
        )}
      </AnimatePresence>
    </div>
  );
}
