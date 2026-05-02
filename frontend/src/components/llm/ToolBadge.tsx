import { CheckCircle2, Loader2, Wrench, XCircle } from "lucide-react";
import type { ToolBadge as ToolBadgeData } from "../../lib/schemas/chat";

interface ToolBadgeProps {
  tool: ToolBadgeData;
}

const STATUS_META = {
  called: { icon: Loader2, spin: true, label: "Looking up", color: "text-muted-foreground" },
  ok: { icon: CheckCircle2, spin: false, label: "Used", color: "text-success" },
  error: { icon: XCircle, spin: false, label: "Failed", color: "text-destructive" },
};

export function ToolBadge({ tool }: ToolBadgeProps) {
  const meta = STATUS_META[tool.status];
  const Icon = meta.icon;
  return (
    <div
      className={`inline-flex items-center gap-1.5 rounded-full bg-muted/50 border px-2.5 py-0.5 text-[10px] font-mono ${meta.color}`}
      title={tool.detail ?? undefined}
    >
      {tool.status === "called" ? (
        <Loader2 className="h-3 w-3 animate-spin" />
      ) : (
        <Icon className="h-3 w-3" />
      )}
      <Wrench className="h-2.5 w-2.5 opacity-50" />
      <span>{tool.name.replace(/_/g, " ")}</span>
    </div>
  );
}
