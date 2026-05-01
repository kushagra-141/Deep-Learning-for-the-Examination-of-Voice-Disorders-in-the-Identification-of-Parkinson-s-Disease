/// <reference types="vite/client" />

// ── Base config ─────────────────────────────────────────────────────────────
export const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api/v1";

const DEFAULT_HEADERS = { "Content-Type": "application/json" };

class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
    public requestId?: string,
    public payload?: unknown,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    credentials: "include",
    ...init,
    headers: { ...DEFAULT_HEADERS, ...(init.headers || {}) },
  });
  if (!response.ok) {
    let payload: unknown = null;
    try {
      payload = await response.json();
    } catch {
      // non-JSON body
    }
    const err = (payload as { error?: { message?: string; request_id?: string } })?.error;
    throw new ApiError(
      err?.message || `${response.status} ${response.statusText}`,
      response.status,
      err?.request_id,
      payload,
    );
  }
  return response.json() as Promise<T>;
}

export { ApiError };

// ── Schemas ─────────────────────────────────────────────────────────────────

export interface ShapContribution {
  feature: string;
  value: number;
  shap: number;
}

export interface ModelPredictionOut {
  model_name: string;
  model_version: string;
  label: number;
  probability: number;
  shap_top?: ShapContribution[] | null;
}

export interface PredictionResponse {
  prediction_id: string;
  created_at: string;
  input_mode: "manual" | "audio" | "batch";
  per_model: ModelPredictionOut[];
  ensemble: ModelPredictionOut;
  primary_model: string;
  disclaimer: string;
}

export type VoiceFeatures = Record<string, number>;

export interface ModelInfo {
  name: string;
  version: string;
  metrics: {
    accuracy: number;
    precision: number;
    recall: number;
    f1: number;
    roc_auc: number;
    confusion_matrix: { tn: number; fp: number; fn: number; tp: number };
    cv_accuracy_mean: number;
    cv_accuracy_std: number;
  };
  hyperparameters: Record<string, unknown>;
  trained_at: string;
}

export interface ConfusionMatrixOut {
  tn: number;
  fp: number;
  fn: number;
  tp: number;
  labels: string[];
}

export interface RocCurve {
  model: string;
  fpr: number[];
  tpr: number[];
  thresholds: number[];
}

export interface PrCurve {
  model: string;
  precision: number[];
  recall: number[];
  thresholds: number[];
}

export interface CalibrationCurve {
  model: string;
  mean_predicted_probability: number[];
  fraction_of_positives: number[];
  n_bins: number;
}

export interface DatasetStats {
  total: number;
  by_class: { healthy: number; parkinsons: number };
  feature_count: number;
  class_balance_pct: number;
}

export interface BoxplotStats {
  min: number;
  q1: number;
  median: number;
  q3: number;
  max: number;
  mean: number;
  std: number;
}

export interface FeatureDistribution {
  feature: string;
  bins: number[];
  counts: number[];
  by_class: Record<"healthy" | "parkinsons", BoxplotStats>;
}

export interface CorrelationMatrix {
  features: string[];
  matrix: number[][];
}

export interface PCAPoint {
  x: number;
  y: number;
  label: number;
}

export interface PCAProjection {
  components: number;
  explained_variance: number[];
  points: PCAPoint[];
}

export interface FeedbackIn {
  prediction_id: string;
  rating: number;
  comment?: string | null;
}

export interface FeedbackOut {
  received: boolean;
  feedback_id: string;
}

export interface LoginIn {
  username: string;
  password: string;
}

export interface TokenOut {
  access_token: string;
  token_type: string;
  expires_at: string;
}

export interface PaginatedPage<T> {
  items: T[];
  next_cursor: string | null;
  limit: number;
  cursor: string | null;
}

export interface AdminPredictionRow {
  id: string;
  created_at: string;
  input_mode: string;
  model_count: number;
}

export interface AdminFeedbackRow {
  id: string;
  created_at: string;
  prediction_id: string;
  rating: number;
  comment: string | null;
}

export interface AdminAuditRow {
  id: string;
  created_at: string;
  actor: string;
  action: string;
  resource: string | null;
  detail: Record<string, unknown> | null;
}

// ── Predict ─────────────────────────────────────────────────────────────────

export const predictFeatures = (features: VoiceFeatures) =>
  request<PredictionResponse>("/predict/", {
    method: "POST",
    body: JSON.stringify({ features }),
  });

export const predictAudio = async (file: Blob | File): Promise<PredictionResponse> => {
  const formData = new FormData();
  formData.append("file", file, "recording.webm");
  // Multipart: don't set Content-Type — let the browser add the boundary.
  const response = await fetch(`${API_BASE_URL}/audio/predict`, {
    method: "POST",
    body: formData,
    credentials: "include",
  });
  if (!response.ok) {
    const errData = await response.json().catch(() => null);
    throw new ApiError(
      errData?.detail || `Audio prediction failed: ${response.statusText}`,
      response.status,
    );
  }
  return response.json();
};

export const getPredictSample = (label: "0" | "1" | "random" = "random") =>
  request<VoiceFeatures>(`/predict/sample?label=${label}`);

// ── Models ──────────────────────────────────────────────────────────────────

export const getModels = () => request<ModelInfo[]>("/models");

export const getModelComparison = () =>
  request<{ models: ModelInfo[] }>("/models/compare");

export const getConfusionMatrix = (name: string) =>
  request<ConfusionMatrixOut>(`/models/${encodeURIComponent(name)}/confusion-matrix`);

export const getRoc = (name: string) =>
  request<RocCurve>(`/models/${encodeURIComponent(name)}/roc`);

export const getPr = (name: string) =>
  request<PrCurve>(`/models/${encodeURIComponent(name)}/pr`);

export const getCalibration = (name: string, nBins = 10) =>
  request<CalibrationCurve>(
    `/models/${encodeURIComponent(name)}/calibration?n_bins=${nBins}`,
  );

// ── Analytics ───────────────────────────────────────────────────────────────

export const getDatasetStats = () =>
  request<DatasetStats>("/analytics/dataset-stats");

export const getFeatureDistribution = (name: string, bins = 30) =>
  request<FeatureDistribution>(
    `/analytics/feature/${encodeURIComponent(name)}?bins=${bins}`,
  );

export const getCorrelation = () =>
  request<CorrelationMatrix>("/analytics/correlation");

export const getPCA = (components: 2 | 3 = 2) =>
  request<PCAProjection>(`/analytics/pca?components=${components}`);

// ── Batch ───────────────────────────────────────────────────────────────────

export interface BatchJobCreated {
  job_id: string;
  status_url: string;
}

export interface BatchJobStatus {
  id: string;
  status: "queued" | "running" | "succeeded" | "failed";
  progress: number;
  row_count: number;
  error: string | null;
}

export const submitBatch = async (file: File): Promise<BatchJobCreated> => {
  const formData = new FormData();
  formData.append("file", file, file.name);
  const response = await fetch(`${API_BASE_URL}/batch/`, {
    method: "POST",
    body: formData,
    credentials: "include",
  });
  if (!response.ok) {
    const errData = await response.json().catch(() => null);
    throw new ApiError(
      errData?.detail || `Batch upload failed: ${response.statusText}`,
      response.status,
    );
  }
  return response.json();
};

export const getBatchStatus = (jobId: string) =>
  request<BatchJobStatus>(`/batch/${encodeURIComponent(jobId)}`);

export const batchDownloadUrl = (jobId: string) =>
  `${API_BASE_URL}/batch/${encodeURIComponent(jobId)}/download`;

// ── Feedback ────────────────────────────────────────────────────────────────

export const submitFeedback = (body: FeedbackIn) =>
  request<FeedbackOut>("/feedback/", {
    method: "POST",
    body: JSON.stringify(body),
  });

// ── Auth + Admin ────────────────────────────────────────────────────────────

export const login = (body: LoginIn) =>
  request<TokenOut>("/auth/login", {
    method: "POST",
    body: JSON.stringify(body),
  });

export const logout = () =>
  request<{ ok: boolean }>("/auth/logout", { method: "POST" });

export const getAdminMe = () =>
  request<{ username: string; role: string }>("/admin/me");

export const getAdminPredictions = (cursor?: string, limit = 50) => {
  const qs = new URLSearchParams({ limit: String(limit) });
  if (cursor) qs.set("cursor", cursor);
  return request<PaginatedPage<AdminPredictionRow>>(`/admin/predictions?${qs}`);
};

export const getAdminFeedback = (cursor?: string, limit = 50) => {
  const qs = new URLSearchParams({ limit: String(limit) });
  if (cursor) qs.set("cursor", cursor);
  return request<PaginatedPage<AdminFeedbackRow>>(`/admin/feedback?${qs}`);
};

export const getAdminAuditLog = (cursor?: string, limit = 100) => {
  const qs = new URLSearchParams({ limit: String(limit) });
  if (cursor) qs.set("cursor", cursor);
  return request<PaginatedPage<AdminAuditRow>>(`/admin/audit-log?${qs}`);
};

// ── LLM streaming (unchanged) ───────────────────────────────────────────────

export async function* streamExplanation(
  features: Record<string, number>,
  probability: number,
  inputMode: string,
): AsyncGenerator<string, void, unknown> {
  const response = await fetch(`${API_BASE_URL}/explain/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      features,
      probability,
      input_mode: inputMode,
    }),
    credentials: "include",
  });

  if (!response.ok) throw new ApiError("Failed to connect to explanation service", response.status);
  if (!response.body) throw new Error("Response body is empty");

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n\n");
    buffer = lines.pop() || "";

    for (const line of lines) {
      if (line.startsWith("data: ")) {
        const dataStr = line.slice(6);
        if (dataStr === "[DONE]") return;
        try {
          const data = JSON.parse(dataStr);
          if (data.text) yield data.text;
        } catch (e) {
          console.error("Failed to parse SSE JSON:", e);
        }
      }
    }
  }
}
