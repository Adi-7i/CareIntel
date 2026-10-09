import * as React from "react";
import { Badge } from "@/components/ui/badge";
import { cn } from "cn";

export type EvidenceState = 
  | "PENDING_UPLOAD"
  | "STORED"
  | "QUARANTINED"
  | "READY"
  | "DELETE_PENDING"
  | "DELETED"
  | "DELETE_FAILED"
  | "FAILED";

interface EvidenceStateBadgeProps {
  state: EvidenceState;
  className?: string;
}

export function EvidenceStateBadge({ state, className }: EvidenceStateBadgeProps) {
  let colorClass = "";

  switch (state) {
    case "PENDING_UPLOAD":
      colorClass = "bg-[var(--status-warning-surface)] text-[var(--status-warning-text)] border-[var(--status-warning)]";
      break;
    case "STORED":
      colorClass = "bg-[var(--status-info-surface)] text-[var(--status-info-text)] border-[var(--status-info)]";
      break;
    case "QUARANTINED":
      colorClass = "bg-[var(--status-error-surface)] text-[var(--status-error-text)] border-[var(--status-error)]";
      break;
    case "READY":
      colorClass = "bg-[var(--status-success-surface)] text-[var(--status-success-text)] border-[var(--status-success)]";
      break;
    case "FAILED":
    case "DELETE_FAILED":
      colorClass = "bg-[var(--status-error-surface)] text-[var(--status-error-text)] border-[var(--status-error)]";
      break;
    case "DELETE_PENDING":
    case "DELETED":
      colorClass = "bg-muted text-muted-foreground border-muted-foreground/30";
      break;
  }

  return (
    <Badge variant="outline" className={cn("font-serif text-[11px] font-semibold uppercase tracking-wider rounded-md", colorClass, className)}>
      {state.replace("_", " ")}
    </Badge>
  );
}
