import { useEffect, useRef, useState, useCallback } from "react";
import * as Dialog from "@radix-ui/react-dialog";
import * as SliderPrimitive from "@radix-ui/react-slider";
import { motion } from "framer-motion";
import { X, RotateCcw, ArrowRight, Loader2, SlidersHorizontal } from "lucide-react";
import { Button } from "../ui/button";
import { predictFeatures } from "../../api/client";
import type { PredictionResponse } from "../../api/client";

// ── Dataset percentile ranges (10th–90th) from backend/app/schemas/feature.py ─
const FEATURE_META: Record<string, { min: number; max: number; step: number; label: string }> = {
  "MDVP:Fo(Hz)":      { min: 80,   max: 270,    step: 0.5,    label: "Avg Fundamental Freq" },
  "MDVP:Fhi(Hz)":     { min: 100,  max: 600,    step: 0.5,    label: "Max Fundamental Freq" },
  "MDVP:Flo(Hz)":     { min: 60,   max: 240,    step: 0.5,    label: "Min Fundamental Freq" },
  "MDVP:Jitter(%)":   { min: 0.001,max: 0.033,  step: 0.0001, label: "Jitter %" },
  "MDVP:Jitter(Abs)": { min: 0,    max: 0.00026,step: 0.000001,label: "Absolute Jitter" },
  "MDVP:RAP":         { min: 0.0005,max: 0.021, step: 0.0001, label: "Relative Amplitude Perturbation" },
  "MDVP:PPQ":         { min: 0.0006,max: 0.019, step: 0.0001, label: "Period Perturbation Quotient" },
  "Jitter:DDP":       { min: 0.001, max: 0.062, step: 0.0001, label: "Jitter DDP" },
  "MDVP:Shimmer":     { min: 0.009, max: 0.120, step: 0.001,  label: "Local Shimmer" },
  "MDVP:Shimmer(dB)": { min: 0.08,  max: 1.17,  step: 0.01,   label: "Shimmer (dB)" },
  "Shimmer:APQ3":     { min: 0.004, max: 0.056, step: 0.001,  label: "3-pt Amplitude Perturbation" },
  "Shimmer:APQ5":     { min: 0.006, max: 0.070, step: 0.001,  label: "5-pt Amplitude Perturbation" },
  "MDVP:APQ":         { min: 0.007, max: 0.138, step: 0.001,  label: "11-pt Amplitude Perturbation" },
  "Shimmer:DDA":      { min: 0.013, max: 0.169, step: 0.001,  label: "Shimmer DDA" },
  "NHR":              { min: 0,     max: 0.31,  step: 0.001,  label: "Noise-to-Harmonics Ratio" },
  "HNR":              { min: 8,     max: 34,    step: 0.1,    label: "Harmonics-to-Noise Ratio" },
  "RPDE":             { min: 0.25,  max: 0.69,  step: 0.01,   label: "Recurrence Period Density" },
  "DFA":              { min: 0.57,  max: 0.99,  step: 0.01,   label: "Detrended Fluctuation Analysis" },
  "spread1":          { min: -7.96, max: -2.43, step: 0.01,   label: "Nonlinear F0 Variation 1" },
  "spread2":          { min: 0.006, max: 0.45,  step: 0.001,  label: "Nonlinear F0 Variation 2" },
  "D2":               { min: 1.0,   max: 3.7,   step: 0.01,   label: "Correlation Dimension" },
  "PPE":              { min: 0.04,  max: 0.53,  step: 0.001,  label: "Pitch Period Entropy" },
};

const FEATURE_ORDER = Object.keys(FEATURE_META);

function useDebounce<T>(value: T, delay: number): T {
  const [debouncedValue, setDebouncedValue] = useState(value);
  useEffect(() => {
    const timer = setTimeout(() => setDebouncedValue(value), delay);
    return () => clearTimeout(timer);
  }, [value, delay]);
  return debouncedValue;
}

function ProbabilityGauge({ prob, prevProb }: { prob: number; prevProb: number }) {
  const delta = prob - prevProb;
  const pct = Math.round(prob * 100);
  const color = prob >= 0.7 ? "text-destructive" : prob >= 0.4 ? "text-warning" : "text-success";
  const barColor = prob >= 0.7 ? "bg-destructive" : prob >= 0.4 ? "bg-warning" : "bg-success";

  return (
    <div className="flex flex-col items-center gap-3">
      <div className={`text-5xl font-black tabular-nums ${color}`}>
        {pct}%
      </div>
      {Math.abs(delta) > 0.001 && (
        <div className={`text-sm font-medium flex items-center gap-1 ${delta > 0 ? "text-destructive" : "text-success"}`}>
          {delta > 0 ? "▲" : "▼"} {(Math.abs(delta) * 100).toFixed(1)}% from baseline
        </div>
      )}
      <div className="w-full bg-muted rounded-full h-2 overflow-hidden">
        <motion.div
          className={`h-full rounded-full ${barColor}`}
          animate={{ width: `${pct}%` }}
          transition={{ duration: 0.35, ease: "easeOut" }}
        />
      </div>
      <p className="text-xs text-muted-foreground">Ensemble probability of Parkinson's</p>
    </div>
  );
}

interface WhatIfDrawerProps {
  baseline: Record<string, number>;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onApply: (values: Record<string, number>) => void;
}

export function WhatIfDrawer({ baseline, open, onOpenChange, onApply }: WhatIfDrawerProps) {
  const [current, setCurrent] = useState<Record<string, number>>(baseline);
  const [result, setResult] = useState<PredictionResponse | null>(null);
  const [baselineResult, setBaselineResult] = useState<PredictionResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const firstLoad = useRef(true);

  const debouncedCurrent = useDebounce(current, 250);

  // Reset when drawer opens with new baseline
  useEffect(() => {
    if (open) {
      setCurrent({ ...baseline });
      setResult(null);
      setBaselineResult(null);
      firstLoad.current = true;
    }
  }, [open, baseline]);

  // Auto-predict when values change
  const fetchPrediction = useCallback(async (values: Record<string, number>) => {
    const hasValues = Object.values(values).some(v => v !== 0);
    if (!hasValues) return;
    setIsLoading(true);
    try {
      const res = await predictFeatures(values);
      if (firstLoad.current) {
        setBaselineResult(res);
        firstLoad.current = false;
      }
      setResult(res);
    } catch {
      // Silently fail — user sees stale value
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    if (open) {
      fetchPrediction(debouncedCurrent);
    }
  }, [debouncedCurrent, open, fetchPrediction]);

  const handleSlider = (feature: string, value: number[]) => {
    setCurrent(prev => {
      const next = { ...prev };
      next[feature] = value[0] as number;
      return next;
    });
  };

  const handleReset = () => {
    setCurrent({ ...baseline });
  };

  return (
    <Dialog.Root open={open} onOpenChange={onOpenChange}>
      <Dialog.Portal>
        <Dialog.Overlay asChild>
          <motion.div
            className="fixed inset-0 bg-black/40 backdrop-blur-sm z-50"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
          />
        </Dialog.Overlay>
        <Dialog.Content asChild>
          <motion.div
            className="fixed inset-y-0 right-0 z-50 w-full max-w-md bg-background border-l shadow-2xl flex flex-col focus:outline-none"
            initial={{ x: "100%" }}
            animate={{ x: 0 }}
            exit={{ x: "100%" }}
            transition={{ type: "spring", stiffness: 300, damping: 30 }}
          >
            {/* Header */}
            <div className="flex items-center justify-between p-5 border-b shrink-0">
              <div className="flex items-center gap-2">
                <SlidersHorizontal className="h-5 w-5 text-primary" />
                <Dialog.Title className="font-semibold text-base">What-If Explorer</Dialog.Title>
              </div>
              <Dialog.Close asChild>
                <button className="rounded-md p-1.5 hover:bg-accent transition-colors">
                  <X className="h-4 w-4" />
                </button>
              </Dialog.Close>
            </div>

            {/* Probability gauge */}
            <div className="p-5 border-b shrink-0">
              {isLoading ? (
                <div className="flex justify-center py-4">
                  <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
                </div>
              ) : result ? (
                <ProbabilityGauge
                  prob={result.ensemble.probability}
                  prevProb={baselineResult?.ensemble.probability ?? result.ensemble.probability}
                />
              ) : (
                <p className="text-center text-sm text-muted-foreground py-4">
                  Adjust sliders to see live predictions...
                </p>
              )}
            </div>

            {/* Sliders */}
            <div className="overflow-y-auto flex-1 p-5 space-y-5">
              <p className="text-xs text-muted-foreground">
                Drag any slider to re-run the ensemble prediction in real time.
              </p>
              {FEATURE_ORDER.map((feat) => {
                const meta = FEATURE_META[feat];
                if (!meta) return null;
                const value = current[feat] ?? baseline[feat] ?? (meta.min + meta.max) / 2;
                const changed = Math.abs(value - (baseline[feat] ?? value)) > meta.step * 0.5;

                return (
                  <div key={feat} className="space-y-2">
                    <div className="flex justify-between items-center">
                      <label className={`text-xs font-mono font-medium ${changed ? "text-primary" : "text-muted-foreground"}`}>
                        {feat}
                        {changed && <span className="ml-1 text-primary">●</span>}
                      </label>
                      <span className="text-xs tabular-nums font-mono text-foreground">
                        {value.toFixed(feat.includes("Hz") ? 1 : 5)}
                      </span>
                    </div>
                    <SliderPrimitive.Root
                      min={meta.min}
                      max={meta.max}
                      step={meta.step}
                      value={[value]}
                      onValueChange={(v) => handleSlider(feat, v)}
                      className="relative flex w-full touch-none select-none items-center"
                    >
                      <SliderPrimitive.Track className="relative h-1.5 w-full grow overflow-hidden rounded-full bg-muted">
                        <SliderPrimitive.Range className="absolute h-full bg-primary" />
                      </SliderPrimitive.Track>
                      <SliderPrimitive.Thumb className="block h-4 w-4 rounded-full border-2 border-primary bg-background shadow transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:pointer-events-none disabled:opacity-50 hover:border-primary/80 cursor-grab active:cursor-grabbing" />
                    </SliderPrimitive.Root>
                    <div className="flex justify-between text-[10px] text-muted-foreground">
                      <span>{meta.min}</span>
                      <span className="text-center text-[9px] opacity-60">{meta.label}</span>
                      <span>{meta.max}</span>
                    </div>
                  </div>
                );
              })}
            </div>

            {/* Footer actions */}
            <div className="p-5 border-t shrink-0 flex gap-3">
              <Button variant="outline" size="sm" className="flex-1" onClick={handleReset}>
                <RotateCcw className="h-4 w-4 mr-2" />
                Reset
              </Button>
              <Button
                size="sm"
                className="flex-1"
                onClick={() => {
                  onApply(current);
                  onOpenChange(false);
                }}
              >
                Apply to Form
                <ArrowRight className="h-4 w-4 ml-2" />
              </Button>
            </div>
          </motion.div>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}
