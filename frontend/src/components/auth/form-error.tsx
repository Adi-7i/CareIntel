import * as React from "react";
import { AlertCircle } from "lucide-react";
import { cn } from "cn";

interface FormErrorProps {
  id: string;
  message?: string;
  className?: string;
}

export function FormError({ id, message, className }: FormErrorProps) {
  if (!message) return null;

  return (
    <div
      id={id}
      role="alert"
      className={cn("flex items-center gap-2 mt-2 text-sm text-[var(--status-error-text)] font-serif", className)}
    >
      <AlertCircle className="size-4 shrink-0" aria-hidden="true" />
      <span>{message}</span>
    </div>
  );
}
