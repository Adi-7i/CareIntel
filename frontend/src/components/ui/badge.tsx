import * as React from "react"
import { cva, type VariantProps } from "class-variance-authority"
import { cn } from "cn"

const badgeVariants = cva(
  "inline-flex items-center rounded-xs border px-2.5 py-0.5 text-xs font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2",
  {
    variants: {
      variant: {
        neutral: "border-border bg-muted text-muted-foreground",
        success: "border-[var(--status-success-surface)] bg-[var(--status-success-surface)] text-[var(--status-success-text)]",
        warning: "border-[var(--status-warning-surface)] bg-[var(--status-warning-surface)] text-[var(--status-warning-text)]",
        error: "border-[var(--status-error-surface)] bg-[var(--status-error-surface)] text-[var(--status-error-text)]",
        info: "border-[var(--status-info-surface)] bg-[var(--status-info-surface)] text-[var(--status-info-text)]",
        outline: "text-foreground",
      },
    },
    defaultVariants: {
      variant: "neutral",
    },
  }
)

function Badge({
  className,
  variant,
  ...props
}: React.ComponentProps<"div"> & VariantProps<typeof badgeVariants>) {
  return (
    <div className={cn(badgeVariants({ variant }), className)} {...props} />
  )
}

export { Badge, badgeVariants }
