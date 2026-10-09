import * as React from "react"
import { cn } from "cn"

function FormField({ className, ...props }: React.ComponentProps<"div">) {
  return (
    <div
      className={cn("flex flex-col gap-1.5", className)}
      {...props}
    />
  )
}

export { FormField }
