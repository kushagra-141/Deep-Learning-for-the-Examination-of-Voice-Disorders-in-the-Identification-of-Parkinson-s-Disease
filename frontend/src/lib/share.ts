/**
 * Share-link encoding for prediction inputs.
 *
 * Strategy: pack the 22 features as a compact JSON object, then base64url-encode
 * it into a single `q` query param. URLs stay under ~1.5 KB, well within
 * browser/server limits, while keeping decoding deterministic.
 *
 * URL shape:
 *   /predict?q=<base64url(JSON)>           — prefill only
 *   /predict?q=<base64url(JSON)>&auto=1    — prefill and re-submit
 */

const FEATURE_KEYS = [
  "MDVP:Fo(Hz)", "MDVP:Fhi(Hz)", "MDVP:Flo(Hz)",
  "MDVP:Jitter(%)", "MDVP:Jitter(Abs)", "MDVP:RAP", "MDVP:PPQ", "Jitter:DDP",
  "MDVP:Shimmer", "MDVP:Shimmer(dB)", "Shimmer:APQ3", "Shimmer:APQ5", "MDVP:APQ", "Shimmer:DDA",
  "NHR", "HNR",
  "RPDE", "DFA", "spread1", "spread2", "D2", "PPE",
] as const;

function toBase64Url(input: string): string {
  // btoa expects latin-1; use TextEncoder for safety with arbitrary Unicode,
  // even though our payload is ASCII JSON.
  const bytes = new TextEncoder().encode(input);
  let bin = "";
  for (let i = 0; i < bytes.length; i++) bin += String.fromCharCode(bytes[i] as number);
  return btoa(bin).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
}

function fromBase64Url(input: string): string {
  const padded = input.replace(/-/g, "+").replace(/_/g, "/") + "=".repeat((4 - (input.length % 4)) % 4);
  const bin = atob(padded);
  const bytes = new Uint8Array(bin.length);
  for (let i = 0; i < bin.length; i++) bytes[i] = bin.charCodeAt(i);
  return new TextDecoder().decode(bytes);
}

export interface SharePayload {
  features: Record<string, number>;
  /** Optional ensemble probability captured at share time, for display only. */
  probability?: number | undefined;
}

export function encodeShare(payload: SharePayload): string {
  // Keep only known feature keys to avoid leaking unrelated form fields.
  const filtered: Record<string, number> = {};
  for (const k of FEATURE_KEYS) {
    const v = payload.features[k];
    if (typeof v === "number" && Number.isFinite(v)) filtered[k] = v;
  }
  const body = {
    v: 1,
    f: filtered,
    ...(payload.probability !== undefined ? { p: Number(payload.probability.toFixed(4)) } : {}),
  };
  return toBase64Url(JSON.stringify(body));
}

export function decodeShare(token: string): SharePayload | null {
  try {
    const json = fromBase64Url(token);
    const obj = JSON.parse(json) as { v?: number; f?: Record<string, unknown>; p?: number };
    if (obj.v !== 1 || !obj.f || typeof obj.f !== "object") return null;
    const features: Record<string, number> = {};
    for (const k of FEATURE_KEYS) {
      const raw = (obj.f as Record<string, unknown>)[k];
      if (typeof raw === "number" && Number.isFinite(raw)) features[k] = raw;
    }
    if (Object.keys(features).length === 0) return null;
    return {
      features,
      probability: typeof obj.p === "number" && Number.isFinite(obj.p) ? obj.p : undefined,
    };
  } catch {
    return null;
  }
}

export interface BuildShareUrlOptions {
  /** When true, append `&auto=1` so the receiving page re-submits on load. */
  autoSubmit?: boolean;
  /** Override the page path; defaults to `/predict`. */
  path?: string;
  /** Override the origin (useful for SSR/tests); defaults to `window.location.origin`. */
  origin?: string;
}

export function buildShareUrl(payload: SharePayload, opts: BuildShareUrlOptions = {}): string {
  const token = encodeShare(payload);
  const origin = opts.origin ?? (typeof window !== "undefined" ? window.location.origin : "");
  const path = opts.path ?? "/predict";
  const params = new URLSearchParams({ q: token });
  if (opts.autoSubmit) params.set("auto", "1");
  return `${origin}${path}?${params.toString()}`;
}

/**
 * Read share params from the current URL. Returns `null` if no `q` param is
 * present or if it fails to decode.
 */
export function readShareFromLocation(search: string): { payload: SharePayload; autoSubmit: boolean } | null {
  const params = new URLSearchParams(search);
  const q = params.get("q");
  if (!q) return null;
  const payload = decodeShare(q);
  if (!payload) return null;
  return { payload, autoSubmit: params.get("auto") === "1" };
}

export async function copyToClipboard(text: string): Promise<boolean> {
  try {
    if (typeof navigator !== "undefined" && navigator.clipboard?.writeText) {
      await navigator.clipboard.writeText(text);
      return true;
    }
  } catch {
    // Fall through to the legacy path below.
  }

  // Fallback for non-secure contexts and older browsers.
  if (typeof document === "undefined") return false;
  const ta = document.createElement("textarea");
  ta.value = text;
  ta.style.position = "fixed";
  ta.style.opacity = "0";
  document.body.appendChild(ta);
  ta.focus();
  ta.select();
  let ok = false;
  try {
    ok = document.execCommand("copy");
  } catch {
    ok = false;
  }
  document.body.removeChild(ta);
  return ok;
}
