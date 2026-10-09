import * as React from "react";
import { Clock } from "lucide-react";
import { EmptyState } from "@/components/ui/empty-state";

export function TimelineList() {
  return (
    <div className="space-y-6">
      <div className="border rounded-lg bg-surface shadow-sm overflow-hidden">
        <div className="bg-muted/30 px-6 py-4 border-b flex justify-between items-center">
          <h2 className="font-serif font-semibold text-secondary flex items-center gap-2">
            <Clock className="size-4" />
            Clinical Timeline
          </h2>
        </div>
        
        <div className="p-6">
          <EmptyState
            icon={<Clock className="size-8" />}
            title="No Timeline Events"
            description="Run clinical structuring to generate timeline events for this case."
          />
        </div>
      </div>
    </div>
  );
}
