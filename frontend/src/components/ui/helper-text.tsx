import * as React from "react"
import { cn } from "cn"

interface HelperTextProps extends React.ComponentProps<"p"> {
  variant?: "default" | "error" | "success"
}

function HelperText({ className, variant = "default", ...props }: HelperTextProps) {
  return (
    <p
      className={cn(
        "text-xs mt-1",
        {
          "text-muted-foreground": variant === "default",
          "text-[var(--status-error-text)]": variant === "error",
          "text-[var(--status-success-text)]": variant === "success",
        },
        className
      )}
      {...props}
    />
  )
}

export { HelperText }
