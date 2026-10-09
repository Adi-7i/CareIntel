import * as React from "react";
import { Badge } from "@/components/ui/badge";

type ReviewQueueStatus = 
  | "PENDING_ASSIGNMENT"
  | "ASSIGNED"
  | "IN_REVIEW"
  | "CLARIFICATION_PENDING"
  | "REVIEW_COMPLETE"
  | "ESCALATED";

export function ReviewQueueBadge({ status }: { status: string }) {
  let label = status;
  let variant: "outline" | "error" | "neutral" | "success" | "warning" | "info" = "outline";
  let colorClass = "";

  switch (status as ReviewQueueStatus) {
    case "PENDING_ASSIGNMENT":
      label = "Pending Assignment";
      variant = "neutral";
      break;
    case "ASSIGNED":
      label = "Assigned";
      variant = "neutral";
      break;
    case "IN_REVIEW":
      label = "In Review";
      colorClass = "bg-[var(--status-info)] text-white hover:bg-[var(--status-info)]/90";
      variant = "info";
      break;
    case "CLARIFICATION_PENDING":
      label = "Clarification Pending";
      colorClass = "bg-[var(--status-warning)] text-[var(--status-warning-text)] hover:bg-[var(--status-warning)]/90";
      variant = "warning";
      break;
    case "REVIEW_COMPLETE":
      label = "Review Complete";
      colorClass = "bg-[var(--status-success)] text-white hover:bg-[var(--status-success)]/90";
      variant = "success";
      break;
    case "ESCALATED":
      label = "Escalated";
      variant = "error";
      break;
  }

  return (
    <Badge variant={variant} className={colorClass}>
      {label}
    </Badge>
  );
}
