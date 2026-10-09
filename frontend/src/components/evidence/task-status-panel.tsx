import * as React from "react";
import { Activity } from "lucide-react";
import { EmptyState } from "@/components/ui/empty-state";

export function TaskStatusPanel() {
  return (
    <div className="space-y-6">
      <div className="rounded-md bg-[var(--status-info-surface)] border border-[var(--status-info)] p-4 mb-6">
        <p className="font-serif text-sm text-[var(--status-info-text)] font-semibold mb-1">
          Backend Integration Required
        </p>
        <p className="font-serif text-sm text-[var(--status-info-text)]">
          This panel will display task status strings and timestamps exactly as returned by AsyncTaskResponse. No fabricated progress bars are implemented.
        </p>
      </div>

      <div className="border rounded-lg bg-surface shadow-sm overflow-hidden">
        <div className="bg-muted/30 px-6 py-4 border-b flex justify-between items-center">
          <h2 className="font-serif font-semibold text-secondary flex items-center gap-2">
            <Activity className="size-4" />
            Processing Tasks
          </h2>
        </div>
        
        <div className="p-6">
          <EmptyState
            icon={<Activity className="size-8" />}
            title="No Tasks Available"
            description="Processing tasks for the selected evidence will appear here when connected to the backend."
          />
        </div>
      </div>
    </div>
  );
}
