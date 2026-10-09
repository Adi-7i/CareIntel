import * as React from "react";
import { Laptop, Database } from "lucide-react";
import { EmptyState } from "@/components/ui/empty-state";

export function ReviewWorkspacePanel() {
  return (
    <div className="border rounded-lg bg-surface shadow-sm overflow-hidden">
      <div className="bg-muted/30 px-6 py-4 border-b flex justify-between items-center">
        <h2 className="font-serif font-semibold text-secondary flex items-center gap-2">
          <Laptop className="size-4" />
          Review Workspace
        </h2>
      </div>
      
      <div className="p-6">
        <div className="rounded-md bg-muted border p-4 mb-6">
          <p className="font-serif text-sm text-secondary font-semibold mb-1">
            Dynamic Workspace Structure
          </p>
          <p className="font-serif text-sm text-muted-foreground">
            The backend returns workspace data as an untyped dictionary (<code>dict[str, Any]</code>). The workspace layout will be dynamically rendered based on backend payloads after integration. No mock layout is assumed here.
          </p>
        </div>
        
        <EmptyState
          icon={<Database className="size-8" />}
          title="Workspace Unavailable"
          description="Connect to the backend to retrieve and render the active review workspace."
        />
      </div>
    </div>
  );
}
