import * as React from "react";
import { Badge } from "@/components/ui/badge";

export function EscalationStatusBadge({ status }: { status: string }) {
  let label = status;
  let variant: "outline" | "error" | "neutral" | "success" | "warning" | "info" = "outline";
  let colorClass = "";

  switch (status) {
    case "OPEN":
      label = "Open";
      colorClass = "bg-[var(--status-error)] text-[var(--status-error-text)] hover:bg-[var(--status-error)]/90";
      variant = "error";
      break;
    case "ACKNOWLEDGED":
      label = "Acknowledged";
      colorClass = "bg-[var(--status-warning)] text-[var(--status-warning-text)] hover:bg-[var(--status-warning)]/90";
      variant = "warning";
      break;
    case "RESOLVED":
      label = "Resolved";
      colorClass = "bg-[var(--status-success)] text-white hover:bg-[var(--status-success)]/90";
      variant = "success";
      break;
  }

  return (
    <Badge variant={variant} className={colorClass}>
      {label}
    </Badge>
  );
}
