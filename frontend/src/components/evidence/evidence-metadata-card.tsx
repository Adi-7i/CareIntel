import * as React from "react";
import { Download, Info, HardDrive } from "lucide-react";
import { Button } from "@/components/ui/button";
import { EmptyState } from "@/components/ui/empty-state";

export function EvidenceMetadataCard() {
  return (
    <div className="space-y-6">
      <div className="rounded-md bg-[var(--status-info-surface)] border border-[var(--status-info)] p-4 mb-6">
        <p className="font-serif text-sm text-[var(--status-info-text)] font-semibold mb-1">
          Backend Integration Required
        </p>
        <p className="font-serif text-sm text-[var(--status-info-text)]">
          This panel is prepared to display the 12 verified fields from EvidenceResponse. Real metadata will appear once connected.
        </p>
      </div>

      <div className="border rounded-lg bg-surface shadow-sm overflow-hidden">
        <div className="bg-muted/30 px-6 py-4 border-b flex justify-between items-center">
          <h2 className="font-serif font-semibold text-secondary flex items-center gap-2">
            <Info className="size-4" />
            Evidence Metadata
          </h2>
        </div>
        
        <div className="p-6">
          <EmptyState
            icon={<HardDrive className="size-8" />}
            title="No Evidence Selected"
            description="Select an evidence record to view its complete metadata and access download capabilities."
            action={
              <Button disabled variant="outline" className="mt-2">
                <Download className="mr-2 size-4" />
                Download File
              </Button>
            }
          />
        </div>
      </div>
    </div>
  );
}
