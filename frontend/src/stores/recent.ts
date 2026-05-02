import { create } from "zustand";
import { persist, createJSONStorage } from "zustand/middleware";

export interface RecentPrediction {
  /** Backend prediction_id (UUID). May be empty for offline/local-only entries. */
  predictionId: string;
  /** ISO 8601 timestamp of when the user submitted. */
  createdAt: string;
  /** Ensemble probability of Parkinson's (0..1). */
  probability: number;
  /** Risk band derived from probability (low / borderline / high). */
  riskLabel: "Low Risk" | "Borderline" | "High Risk";
  /** Source — manual feature entry, audio recording, or batch row. */
  inputMode: "manual" | "audio" | "batch";
  /** Snapshot of the 22 features that produced this result. Replayable. */
  features: Record<string, number>;
  /** Optional name of the primary model used. */
  primaryModel?: string;
}

const MAX_ENTRIES = 10;

interface RecentState {
  items: RecentPrediction[];
  add: (entry: RecentPrediction) => void;
  remove: (predictionId: string) => void;
  clear: () => void;
}

export const useRecentPredictions = create<RecentState>()(
  persist(
    (set) => ({
      items: [],
      add: (entry) =>
        set((state) => {
          const filtered = state.items.filter(
            (i) =>
              // Drop any prior entry sharing this prediction_id (re-submits replace older copies).
              !(entry.predictionId && i.predictionId === entry.predictionId),
          );
          const next = [entry, ...filtered].slice(0, MAX_ENTRIES);
          return { items: next };
        }),
      remove: (predictionId) =>
        set((state) => ({
          items: state.items.filter((i) => i.predictionId !== predictionId),
        })),
      clear: () => set({ items: [] }),
    }),
    {
      name: "parkinsons-recent-predictions",
      storage: createJSONStorage(() => localStorage),
      version: 1,
    },
  ),
);

export function riskFromProbability(prob: number): RecentPrediction["riskLabel"] {
  if (prob >= 0.7) return "High Risk";
  if (prob >= 0.4) return "Borderline";
  return "Low Risk";
}
