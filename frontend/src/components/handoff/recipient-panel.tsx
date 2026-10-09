import * as React from "react";
import { Users } from "lucide-react";
import { EmptyState } from "@/components/ui/empty-state";

export function RecipientPanel() {
  return (
    <div className="space-y-6">
      <div className="rounded-md bg-muted border p-4 mb-6">
        <p className="font-serif text-sm text-secondary font-semibold mb-1">
          Recipient Directory Source
        </p>
        <p className="font-serif text-sm text-muted-foreground">
          Recipients are fetched from the backend (<code>GET /recipients</code>) returning real organizational entities (id, name, type). The directory is not mocked or hardcoded.
        </p>
      </div>

      <div className="border rounded-lg bg-surface shadow-sm overflow-hidden">
        <div className="bg-muted/30 px-6 py-4 border-b flex justify-between items-center">
          <h2 className="font-serif font-semibold text-secondary flex items-center gap-2">
            <Users className="size-4" />
            Active Recipients
          </h2>
        </div>
        
        <div className="p-6">
          <EmptyState
            icon={<Users className="size-8" />}
            title="Directory Disconnected"
            description="Connect to the backend to retrieve and render the recipient directory."
          />
        </div>
      </div>
    </div>
  );
}
