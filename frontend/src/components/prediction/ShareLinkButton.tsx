import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Check, Link2, Loader2, Share2 } from "lucide-react";
import { Button } from "../ui/button";
import { buildShareUrl, copyToClipboard, type SharePayload } from "../../lib/share";

interface ShareLinkButtonProps {
  features: Record<string, number>;
  probability?: number;
  /** When true, the generated link includes `&auto=1` for instant re-submit. */
  autoSubmit?: boolean;
  className?: string;
}

export function ShareLinkButton({
  features,
  probability,
  autoSubmit = false,
  className,
}: ShareLinkButtonProps) {
  const [status, setStatus] = useState<"idle" | "copying" | "copied" | "failed">("idle");

  const handleClick = async () => {
    if (status === "copying") return;
    setStatus("copying");
    const payload: SharePayload = { features, probability };
    const url = buildShareUrl(payload, { autoSubmit });
    const ok = await copyToClipboard(url);
    setStatus(ok ? "copied" : "failed");
    setTimeout(() => setStatus("idle"), 2200);
  };

  return (
    <Button
      type="button"
      variant="outline"
      className={className}
      onClick={handleClick}
      disabled={Object.keys(features).length === 0}
      aria-label="Copy a shareable link to this prediction"
    >
      <AnimatePresence mode="wait" initial={false}>
        {status === "copying" ? (
          <motion.span
            key="copying"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="flex items-center"
          >
            <Loader2 className="h-4 w-4 mr-2 animate-spin" />
            Copying…
          </motion.span>
        ) : status === "copied" ? (
          <motion.span
            key="copied"
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0 }}
            className="flex items-center text-success"
          >
            <Check className="h-4 w-4 mr-2" />
            Link copied
          </motion.span>
        ) : status === "failed" ? (
          <motion.span
            key="failed"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="flex items-center text-destructive"
          >
            <Link2 className="h-4 w-4 mr-2" />
            Copy failed
          </motion.span>
        ) : (
          <motion.span
            key="idle"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="flex items-center"
          >
            <Share2 className="h-4 w-4 mr-2" />
            Copy share link
          </motion.span>
        )}
      </AnimatePresence>
    </Button>
  );
}
