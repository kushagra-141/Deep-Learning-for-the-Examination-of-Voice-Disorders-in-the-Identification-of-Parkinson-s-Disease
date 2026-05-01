import { useMutation } from "@tanstack/react-query";
import { predictFeatures, PredictionResponse } from "../api/client";

export function usePrediction() {
  return useMutation<PredictionResponse, Error, Record<string, number>>({
    mutationFn: (features) => predictFeatures(features),
  });
}
