import { motion, AnimatePresence } from "framer-motion";
import { AlertTriangle, Download, FileSpreadsheet, RotateCcw } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../components/ui/card";
import { Badge } from "../components/ui/badge";
import { Button } from "../components/ui/button";
import { BatchUploader } from "../components/batch/BatchUploader";
import { BatchProgress } from "../components/batch/BatchProgress";
import { useBatchJob } from "../hooks/useBatchJob";

const REQUIRED_COLUMNS = [
  "MDVP:Fo(Hz)", "MDVP:Fhi(Hz)", "MDVP:Flo(Hz)",
  "MDVP:Jitter(%)", "MDVP:Jitter(Abs)", "MDVP:RAP", "MDVP:PPQ", "Jitter:DDP",
  "MDVP:Shimmer", "MDVP:Shimmer(dB)", "Shimmer:APQ3", "Shimmer:APQ5", "MDVP:APQ", "Shimmer:DDA",
  "NHR", "HNR",
  "RPDE", "DFA", "spread1", "spread2", "D2", "PPE",
];

export default function BatchPage() {
  const { phase, submit, reset, downloadUrl } = useBatchJob();

  const isBusy = phase.kind === "uploading" || phase.kind === "polling";

  return (
    <div className="container py-8 max-w-5xl mx-auto">
      <div className="flex flex-col gap-2 mb-8">
        <Badge variant="outline" className="text-xs w-fit">
          <FileSpreadsheet className="h-3 w-3 mr-1" />
          Batch Mode
        </Badge>
        <h1 className="text-3xl font-bold tracking-tight">Batch Prediction</h1>
        <p className="text-muted-foreground">
          Upload a CSV of acoustic features. We'll run the ensemble across every row and
          give you back a CSV with the predictions appended.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Upload CSV</CardTitle>
              <CardDescription>
                The file must contain a header row with all 22 feature names below.
                Rows missing required columns will be skipped.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <BatchUploader onSelect={submit} disabled={isBusy} />

              <AnimatePresence mode="wait">
                {phase.kind === "uploading" && (
                  <motion.p
                    key="uploading"
                    initial={{ opacity: 0, y: 4 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0 }}
                    className="text-xs text-muted-foreground"
                  >
                    Uploading <span className="font-mono">{phase.filename}</span>…
                  </motion.p>
                )}
              </AnimatePresence>
            </CardContent>
          </Card>

          <AnimatePresence>
            {(phase.kind === "polling" || phase.kind === "done") && (
              <motion.div
                key="progress"
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0 }}
              >
                <BatchProgress status={phase.status} filename={phase.filename} />
              </motion.div>
            )}
          </AnimatePresence>

          <AnimatePresence>
            {phase.kind === "done" && downloadUrl && (
              <motion.div
                key="done-actions"
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0 }}
              >
                <Card className="border-success/30 bg-success/5">
                  <CardContent className="p-5 flex flex-col sm:flex-row items-start sm:items-center gap-4">
                    <div className="flex-1">
                      <p className="font-semibold text-sm">Predictions ready</p>
                      <p className="text-xs text-muted-foreground mt-0.5">
                        Your CSV now includes <span className="font-mono">prediction_label</span>,{" "}
                        <span className="font-mono">probability</span>, and{" "}
                        <span className="font-mono">primary_model</span> columns.
                      </p>
                    </div>
                    <div className="flex gap-2 w-full sm:w-auto">
                      <Button asChild>
                        <a href={downloadUrl} download>
                          <Download className="h-4 w-4 mr-2" />
                          Download CSV
                        </a>
                      </Button>
                      <Button variant="outline" onClick={reset}>
                        <RotateCcw className="h-4 w-4 mr-2" />
                        New job
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              </motion.div>
            )}
          </AnimatePresence>

          <AnimatePresence>
            {phase.kind === "error" && (
              <motion.div
                key="error"
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0 }}
              >
                <Card className="border-destructive/30 bg-destructive/5">
                  <CardContent className="p-5 flex flex-col sm:flex-row items-start sm:items-center gap-4">
                    <div className="flex items-start gap-2 flex-1">
                      <AlertTriangle className="h-4 w-4 text-destructive shrink-0 mt-0.5" />
                      <div>
                        <p className="font-semibold text-sm text-destructive">Job failed</p>
                        <p className="text-xs text-muted-foreground mt-0.5 font-mono break-all">
                          {phase.message}
                        </p>
                      </div>
                    </div>
                    <Button variant="outline" onClick={reset}>
                      <RotateCcw className="h-4 w-4 mr-2" />
                      Try again
                    </Button>
                  </CardContent>
                </Card>
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        <Card className="lg:sticky lg:top-24 h-fit">
          <CardHeader>
            <CardTitle className="text-base">Required Columns</CardTitle>
            <CardDescription className="text-xs">
              All 22 columns must be present. Order doesn't matter — we match by header name.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <ul className="grid grid-cols-1 gap-1 max-h-[400px] overflow-y-auto pr-1">
              {REQUIRED_COLUMNS.map((col) => (
                <li
                  key={col}
                  className="text-[11px] font-mono text-muted-foreground bg-muted/30 rounded px-2 py-1"
                >
                  {col}
                </li>
              ))}
            </ul>
            <p className="text-[10px] text-muted-foreground mt-3 leading-relaxed">
              Tip: any extra columns in your file (e.g., <span className="font-mono">subject_id</span>)
              are passed through to the output unchanged.
            </p>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
