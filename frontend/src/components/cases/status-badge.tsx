import * as React from "react";
import { Badge } from "@/components/ui/badge";
import { cn } from "cn";
import type { CaseState } from "@/types";

export type CaseStatus =
  | CaseState
  | "Draft"
  | "Pending Review"
  | "Under Review"
  | "Approved"
  | "Rejected";

interface StatusBadgeProps {
  status: CaseStatus;
  className?: string;
}

export function StatusBadge({ status, className }: StatusBadgeProps) {
  let colorClass = "";

  switch (status) {
    case "CREATED":
    case "Draft":
      colorClass = "bg-[var(--status-info-surface)] text-[var(--status-info-text)] border-[var(--status-info)]";
      break;
    case "CONSENTED":
    case "INPUT_RECEIVED":
      colorClass = "bg-[var(--ci-light-aqua)] text-[var(--ci-teal-700)] border-[var(--ci-aqua)]";
      break;
    case "PROCESSING":
    case "EXTRACTING":
    case "NORMALIZING":
    case "RETRIEVING":
    case "AI_ANALYSIS":
    case "SAFETY_CHECK":
    case "TRIAGE_DRAFT_READY":
      colorClass = "bg-sky-50 text-sky-800 border-sky-300";
      break;
    case "REVIEW_PENDING":
    case "Pending Review":
    case "Under Review":
      colorClass = "bg-[var(--status-warning-surface)] text-[var(--status-warning-text)] border-[var(--status-warning)]";
      break;
    case "REVIEWED":
    case "Approved":
    case "COMPLETED":
      colorClass = "bg-[var(--status-success-surface)] text-[var(--status-success-text)] border-[var(--status-success)]";
      break;
    case "ESCALATED":
      colorClass = "bg-amber-100 text-amber-900 border-amber-400";
      break;
    case "REFERRED":
      colorClass = "bg-purple-50 text-purple-800 border-purple-300";
      break;
    case "FAILED":
    case "Rejected":
      colorClass = "bg-[var(--status-error-surface)] text-[var(--status-error-text)] border-[var(--status-error)]";
      break;
    default:
      colorClass = "bg-slate-100 text-slate-800 border-slate-300";
      break;
  }

  return (
    <Badge
      variant="outline"
      className={cn(
        "font-serif text-[11px] font-semibold uppercase tracking-wider rounded-md",
        colorClass,
        className
      )}
    >
      {status}
    </Badge>
  );
}
