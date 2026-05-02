import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { motion } from "framer-motion";
import { Compass, Eraser } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../components/ui/card";
import { Badge } from "../components/ui/badge";
import { Button } from "../components/ui/button";
import {
  getCorrelation,
  getDatasetStats,
  getFeatureDistribution,
  getPCA,
} from "../api/client";
import { qk } from "../api/queryKeys";
import { PcaScatter, type BrushRect } from "../components/explorer/PcaScatter";
import { CorrelationHeatmap } from "../components/explorer/CorrelationHeatmap";
import { FeatureDistribution } from "../components/explorer/FeatureDistribution";
import { DatasetTable } from "../components/explorer/DatasetTable";

const FEATURE_OPTIONS = [
  "MDVP:Fo(Hz)", "MDVP:Fhi(Hz)", "MDVP:Flo(Hz)",
  "MDVP:Jitter(%)", "MDVP:Jitter(Abs)", "MDVP:RAP", "MDVP:PPQ", "Jitter:DDP",
  "MDVP:Shimmer", "MDVP:Shimmer(dB)", "Shimmer:APQ3", "Shimmer:APQ5", "MDVP:APQ", "Shimmer:DDA",
  "NHR", "HNR",
  "RPDE", "DFA", "spread1", "spread2", "D2", "PPE",
];

export default function ExplorerPage() {
  const [brush, setBrush] = useState<BrushRect | null>(null);
  const [selectedFeature, setSelectedFeature] = useState<string>("MDVP:Fo(Hz)");

  const stats = useQuery({
    queryKey: qk.datasetStats(),
    queryFn: getDatasetStats,
  });
  const pca = useQuery({
    queryKey: qk.pca(2),
    queryFn: () => getPCA(2),
  });
  const correlation = useQuery({
    queryKey: qk.correlation(),
    queryFn: getCorrelation,
  });
  const distribution = useQuery({
    queryKey: qk.featureDistribution(selectedFeature, 30),
    queryFn: () => getFeatureDistribution(selectedFeature, 30),
  });

  const tableRows = useMemo(() => {
    if (!pca.data) return [];
    return pca.data.points.map((p, index) => {
      const inBrush = brush
        ? p.x >= brush.x0 && p.x <= brush.x1 && p.y >= brush.y0 && p.y <= brush.y1
        : false;
      return { ...p, index, inBrush };
    });
  }, [pca.data, brush]);

  return (
    <div className="container py-8 max-w-7xl mx-auto">
      <div className="flex flex-col gap-2 mb-8">
        <Badge variant="outline" className="text-xs w-fit">
          <Compass className="h-3 w-3 mr-1" />
          Dataset Explorer
        </Badge>
        <h1 className="text-3xl font-bold tracking-tight">Explore the Dataset</h1>
        <p className="text-muted-foreground">
          A live view of the UCI Parkinson's voice dataset — {stats.data?.total ?? "—"} rows,{" "}
          {stats.data?.feature_count ?? 22} acoustic features. Class balance:{" "}
          {stats.data ? `${stats.data.class_balance_pct.toFixed(1)}% Parkinson's` : "loading…"}.
        </p>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6 mb-6">
        <Card>
          <CardHeader>
            <div className="flex items-start justify-between gap-2">
              <div>
                <CardTitle className="text-base">PCA Projection</CardTitle>
                <CardDescription className="text-xs">
                  Two-component PCA over standardized features. Each point is a recording.
                </CardDescription>
              </div>
              {brush && (
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  className="text-xs h-8"
                  onClick={() => setBrush(null)}
                >
                  <Eraser className="h-3 w-3 mr-1" />
                  Clear brush
                </Button>
              )}
            </div>
          </CardHeader>
          <CardContent>
            <PcaScatter
              data={pca.data}
              isLoading={pca.isLoading}
              brush={brush}
              onBrushChange={setBrush}
            />
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <div className="flex items-start justify-between gap-3">
              <div>
                <CardTitle className="text-base">Feature Distribution</CardTitle>
                <CardDescription className="text-xs">
                  Histogram of values for the selected feature, with per-class summary statistics.
                </CardDescription>
              </div>
              <select
                aria-label="Select feature"
                value={selectedFeature}
                onChange={(e) => setSelectedFeature(e.target.value)}
                className="text-xs font-mono bg-background border border-input rounded-md h-8 px-2 max-w-[140px]"
              >
                {FEATURE_OPTIONS.map((f) => (
                  <option key={f} value={f}>
                    {f}
                  </option>
                ))}
              </select>
            </div>
          </CardHeader>
          <CardContent>
            <FeatureDistribution
              data={distribution.data}
              isLoading={distribution.isLoading}
            />
          </CardContent>
        </Card>
      </div>

      <Card className="mb-6">
        <CardHeader>
          <CardTitle className="text-base">Correlation Heatmap</CardTitle>
          <CardDescription className="text-xs">
            Pairwise Pearson correlation across all 22 features. Strong red = inversely correlated;
            strong teal = positively correlated.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <CorrelationHeatmap data={correlation.data} isLoading={correlation.isLoading} />
        </CardContent>
      </Card>

      <motion.div
        layout
        transition={{ type: "spring", stiffness: 300, damping: 30 }}
      >
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Dataset Rows</CardTitle>
            <CardDescription className="text-xs">
              Recordings projected to PC1/PC2. Brush the scatter above to filter this table to
              just the points inside your selection.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <DatasetTable rows={tableRows} totalRows={pca.data?.points.length ?? 0} />
          </CardContent>
        </Card>
      </motion.div>
    </div>
  );
}
