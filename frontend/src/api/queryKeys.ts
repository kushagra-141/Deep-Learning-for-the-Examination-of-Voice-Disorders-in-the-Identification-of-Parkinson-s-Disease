/**
 * Centralized React Query key factory.
 *
 * Convention: `[scope, ...args]`. Keep all keys here so cache invalidation
 * stays grep-able — `queryClient.invalidateQueries({ queryKey: qk.models() })`.
 */
export const qk = {
  models: () => ["models"] as const,
  modelComparison: () => ["models", "compare"] as const,
  modelConfusionMatrix: (name: string) => ["models", name, "confusion-matrix"] as const,
  modelRoc: (name: string) => ["models", name, "roc"] as const,
  modelPr: (name: string) => ["models", name, "pr"] as const,
  modelCalibration: (name: string, nBins: number) =>
    ["models", name, "calibration", nBins] as const,

  datasetStats: () => ["analytics", "dataset-stats"] as const,
  featureDistribution: (name: string, bins: number) =>
    ["analytics", "feature", name, bins] as const,
  correlation: () => ["analytics", "correlation"] as const,
  pca: (components: number) => ["analytics", "pca", components] as const,

  predictSample: (label: string) => ["predict", "sample", label] as const,

  batchStatus: (jobId: string) => ["batch", "status", jobId] as const,

  adminMe: () => ["admin", "me"] as const,
  adminPredictions: (cursor: string | null, limit: number) =>
    ["admin", "predictions", cursor, limit] as const,
  adminFeedback: (cursor: string | null, limit: number) =>
    ["admin", "feedback", cursor, limit] as const,
  adminAuditLog: (cursor: string | null, limit: number) =>
    ["admin", "audit-log", cursor, limit] as const,
} as const;
