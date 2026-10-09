import * as React from "react"
import { cn } from "cn"

function Skeleton({
  className,
  ...props
}: React.ComponentProps<"div">) {
  return (
    <div
      className={cn("animate-pulse rounded-md bg-muted/80 motion-reduce:animate-none", className)}
      {...props}
    />
  )
}

export { Skeleton }
