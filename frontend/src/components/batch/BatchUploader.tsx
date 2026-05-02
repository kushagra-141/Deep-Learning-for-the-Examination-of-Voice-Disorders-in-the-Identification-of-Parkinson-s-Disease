import { useCallback, useRef, useState } from "react";
import { motion } from "framer-motion";
import { AlertTriangle, FileSpreadsheet, Upload } from "lucide-react";
import { Button } from "../ui/button";
import { cn } from "../../lib/cn";

const ACCEPTED_TYPES = [".csv", "text/csv", "application/vnd.ms-excel"];
const MAX_BYTES = 2 * 1024 * 1024; // matches backend BATCH_MAX_BYTES

interface BatchUploaderProps {
  onSelect: (file: File) => void;
  disabled?: boolean;
  className?: string;
}

function isCsv(file: File): boolean {
  if (file.name.toLowerCase().endsWith(".csv")) return true;
  return ACCEPTED_TYPES.includes(file.type);
}

export function BatchUploader({ onSelect, disabled, className }: BatchUploaderProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [dragOver, setDragOver] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleFile = useCallback(
    (file: File) => {
      setError(null);
      if (!isCsv(file)) {
        setError("Please upload a .csv file.");
        return;
      }
      if (file.size === 0) {
        setError("The file is empty.");
        return;
      }
      if (file.size > MAX_BYTES) {
        setError(`File too large — limit is ${(MAX_BYTES / 1024).toFixed(0)} KB.`);
        return;
      }
      onSelect(file);
    },
    [onSelect],
  );

  return (
    <div className={cn("space-y-2", className)}>
      <motion.label
        htmlFor="batch-upload-input"
        whileHover={disabled ? {} : { scale: 1.005 }}
        onDragOver={(e) => {
          e.preventDefault();
          if (!disabled) setDragOver(true);
        }}
        onDragLeave={() => setDragOver(false)}
        onDrop={(e) => {
          e.preventDefault();
          setDragOver(false);
          if (disabled) return;
          const file = e.dataTransfer.files?.[0];
          if (file) handleFile(file);
        }}
        className={cn(
          "flex flex-col items-center justify-center gap-3 rounded-lg border-2 border-dashed p-10 text-center cursor-pointer transition-colors",
          dragOver ? "border-primary bg-primary/5" : "border-border bg-muted/30 hover:bg-muted/50",
          disabled && "cursor-not-allowed opacity-60",
        )}
      >
        <div className="rounded-full bg-primary/10 p-3 text-primary">
          <FileSpreadsheet className="h-6 w-6" />
        </div>
        <div className="space-y-1">
          <p className="text-sm font-semibold">Drop a CSV here, or click to browse</p>
          <p className="text-xs text-muted-foreground">
            22 acoustic features per row · up to 10,000 rows · max 2 MB
          </p>
        </div>
        <Button
          type="button"
          variant="outline"
          size="sm"
          disabled={disabled}
          onClick={(e) => {
            e.preventDefault();
            inputRef.current?.click();
          }}
        >
          <Upload className="h-4 w-4 mr-2" />
          Choose file
        </Button>
        <input
          id="batch-upload-input"
          ref={inputRef}
          type="file"
          accept=".csv,text/csv"
          className="hidden"
          disabled={disabled}
          onChange={(e) => {
            const file = e.target.files?.[0];
            if (file) handleFile(file);
            // Reset so the same file can be re-selected later.
            e.target.value = "";
          }}
        />
      </motion.label>
      {error && (
        <p className="text-xs text-destructive flex items-center gap-1.5" role="alert">
          <AlertTriangle className="h-3 w-3" />
          {error}
        </p>
      )}
    </div>
  );
}
