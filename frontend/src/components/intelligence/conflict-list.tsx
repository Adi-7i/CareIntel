import * as React from "react";
import { AlertTriangle } from "lucide-react";
import { EmptyState } from "@/components/ui/empty-state";

export function ConflictList() {
  return (
    <div className="space-y-6">
      <div className="rounded-md bg-muted border p-4 mb-6">
        <p className="font-serif text-sm text-secondary font-semibold mb-1">
          Conflict Detection Scope
        </p>
        <p className="font-serif text-sm text-muted-foreground">
          Conflicts are based on backend evaluation of conflicting facts. The response provides no severity levels or resolution actions.
        </p>
      </div>

      <div className="border rounded-lg bg-surface shadow-sm overflow-hidden">
        <div className="bg-muted/30 px-6 py-4 border-b flex justify-between items-center">
          <h2 className="font-serif font-semibold text-secondary flex items-center gap-2">
            <AlertTriangle className="size-4" />
            Conflicting Information
          </h2>
        </div>
        
        <div className="p-6">
          <EmptyState
            icon={<AlertTriangle className="size-8" />}
            title="No Conflicts Detected"
            description="Run clinical structuring to detect potential conflicts."
          />
        </div>
      </div>
    </div>
  );
}
