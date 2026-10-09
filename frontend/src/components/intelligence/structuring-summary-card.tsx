import * as React from "react";
import { Activity, Clock, AlertTriangle, FileQuestion, HelpCircle, HardDrive } from "lucide-react";
import { EmptyState } from "@/components/ui/empty-state";

export function StructuringSummaryCard() {
  return (
    <div className="space-y-6">
      <div className="rounded-md bg-muted border p-4 mb-6">
        <p className="font-serif text-sm text-secondary font-semibold mb-1">
          Structuring Run Summary — not a clinical narrative
        </p>
        <p className="font-serif text-sm text-muted-foreground">
          These are counts from the structuring run, not a clinical prose summary or AI-generated text.
        </p>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="border rounded-lg bg-surface shadow-sm p-4 flex flex-col items-center justify-center text-center">
          <Clock className="size-6 text-muted-foreground mb-2" />
          <p className="text-3xl font-serif font-semibold text-secondary">--</p>
          <p className="text-xs text-muted-foreground uppercase tracking-wider font-semibold">Timeline Events</p>
        </div>
        
        <div className="border rounded-lg bg-surface shadow-sm p-4 flex flex-col items-center justify-center text-center">
          <AlertTriangle className="size-6 text-muted-foreground mb-2" />
          <p className="text-3xl font-serif font-semibold text-secondary">--</p>
          <p className="text-xs text-muted-foreground uppercase tracking-wider font-semibold">Conflicts</p>
        </div>

        <div className="border rounded-lg bg-surface shadow-sm p-4 flex flex-col items-center justify-center text-center">
          <FileQuestion className="size-6 text-muted-foreground mb-2" />
          <p className="text-3xl font-serif font-semibold text-secondary">--</p>
          <p className="text-xs text-muted-foreground uppercase tracking-wider font-semibold">Missing Info</p>
        </div>

        <div className="border rounded-lg bg-surface shadow-sm p-4 flex flex-col items-center justify-center text-center">
          <HelpCircle className="size-6 text-muted-foreground mb-2" />
          <p className="text-3xl font-serif font-semibold text-secondary">--</p>
          <p className="text-xs text-muted-foreground uppercase tracking-wider font-semibold">Questions</p>
        </div>
      </div>
      
      <div className="border rounded-lg bg-surface shadow-sm overflow-hidden mt-6">
         <div className="bg-muted/30 px-6 py-4 border-b flex justify-between items-center">
          <h2 className="font-serif font-semibold text-secondary flex items-center gap-2">
            <HardDrive className="size-4" />
            Structuring Run Details
          </h2>
        </div>
        <div className="p-6">
          <EmptyState
            icon={<Activity className="size-8" />}
            title="No Evaluation Run Available"
            description="Trigger clinical structuring to view the summary."
          />
        </div>
      </div>
    </div>
  );
}
