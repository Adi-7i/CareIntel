import * as React from "react";
import { Badge } from "@/components/ui/badge";
import { cn } from "cn";

export type CaseStatus = "Draft" | "Pending Review" | "Under Review" | "Approved" | "Rejected";

interface StatusBadgeProps {
  status: CaseStatus;
  className?: string;
}

export function StatusBadge({ status, className }: StatusBadgeProps) {
  let colorClass = "";

  switch (status) {
    case "Draft":
      colorClass = "bg-[var(--status-info-surface)] text-[var(--status-info-text)] border-[var(--status-info)]";
      break;
    case "Pending Review":
      colorClass = "bg-[var(--status-warning-surface)] text-[var(--status-warning-text)] border-[var(--status-warning)]";
      break;
    case "Under Review":
      colorClass = "bg-[var(--ci-light-aqua)] text-[var(--ci-teal-700)] border-[var(--ci-aqua)]";
      break;
    case "Approved":
      colorClass = "bg-[var(--status-success-surface)] text-[var(--status-success-text)] border-[var(--status-success)]";
      break;
    case "Rejected":
      colorClass = "bg-[var(--status-error-surface)] text-[var(--status-error-text)] border-[var(--status-error)]";
      break;
  }

  return (
    <Badge variant="outline" className={cn("font-serif text-[11px] font-semibold uppercase tracking-wider rounded-md", colorClass, className)}>
      {status}
    </Badge>
  );
}
