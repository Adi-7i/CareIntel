import * as React from "react";
import { FileQuestion, HelpCircle } from "lucide-react";
import { EmptyState } from "@/components/ui/empty-state";

export function MissingInfoList() {
  return (
    <div className="space-y-8">
      <div className="space-y-6">
        <div className="border rounded-lg bg-surface shadow-sm overflow-hidden">
          <div className="bg-muted/30 px-6 py-4 border-b flex justify-between items-center">
            <h2 className="font-serif font-semibold text-secondary flex items-center gap-2">
              <FileQuestion className="size-4" />
              Missing Information Requirements
            </h2>
          </div>
          
          <div className="p-6">
            <EmptyState
              icon={<FileQuestion className="size-8" />}
              title="No Missing Information Identified"
              description="Missing items based on the active checklist will appear here."
            />
          </div>
        </div>
      </div>
      
      <div className="space-y-6">
        <div className="border rounded-lg bg-surface shadow-sm overflow-hidden">
          <div className="bg-muted/30 px-6 py-4 border-b flex justify-between items-center">
            <h2 className="font-serif font-semibold text-secondary flex items-center gap-2">
              <HelpCircle className="size-4" />
              Follow-up Questions
            </h2>
          </div>
          
          <div className="p-6">
            <EmptyState
              icon={<HelpCircle className="size-8" />}
              title="No Follow-up Questions"
              description="Questions generated from missing information will appear here."
            />
          </div>
        </div>
      </div>
    </div>
  );
}
