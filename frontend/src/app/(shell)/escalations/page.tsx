import * as React from "react";
import type { Metadata } from "next";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { EscalationForm } from "@/components/escalation/escalation-form";
import { EscalationResolveForm } from "@/components/escalation/escalation-resolve-form";
import { EscalationStatusBadge } from "@/components/escalation/escalation-status-badge";

export const metadata: Metadata = {
  title: "Escalations Workspace | CareIntel",
  description: "Create and resolve clinical case escalations.",
};

export default function EscalationsPage() {
  return (
    <div className="space-y-6 max-w-6xl mx-auto py-2">
      <header>
        <h1 className="font-serif text-3xl font-semibold tracking-tight text-secondary">
          Escalations Workspace
        </h1>
        <p className="mt-1 font-serif text-sm text-muted-foreground">
          Create and resolve human-in-the-loop clinical escalations.
        </p>
      </header>
      
      <div className="rounded-md bg-muted/40 border p-4 mb-6">
        <p className="font-serif text-sm text-secondary font-semibold mb-1">
          System Integration Notice
        </p>
        <p className="font-serif text-sm text-muted-foreground">
          This workspace is prepared for backend integration. Forms validate locally but require an active session and connected backend services. No mock escalation records are displayed.
        </p>
      </div>

      <div className="mb-8 p-4 bg-surface border rounded-lg max-w-md">
        <h2 className="font-serif text-sm font-semibold mb-3">Status Legend</h2>
        <div className="flex gap-2">
          <EscalationStatusBadge status="OPEN" />
          <EscalationStatusBadge status="ACKNOWLEDGED" />
          <EscalationStatusBadge status="RESOLVED" />
        </div>
        <p className="text-xs text-muted-foreground mt-3 font-serif">
          * Note: The &quot;ACKNOWLEDGED&quot; status exists in the domain definition, but no endpoint is currently available to trigger this transition.
        </p>
      </div>

      <Tabs defaultValue="create" className="w-full">
        <TabsList className="mb-4">
          <TabsTrigger value="create">Create Escalation</TabsTrigger>
          <TabsTrigger value="resolve">Resolve Escalation</TabsTrigger>
        </TabsList>
        
        <TabsContent value="create" className="space-y-8">
          <div className="border rounded-lg bg-surface shadow-sm overflow-hidden">
            <div className="bg-muted/30 px-6 py-4 border-b">
              <h2 className="font-serif font-semibold text-secondary">Trigger New Escalation</h2>
            </div>
            <div className="p-6">
              <EscalationForm />
            </div>
          </div>
        </TabsContent>
        
        <TabsContent value="resolve" className="space-y-8">
          <div className="border rounded-lg bg-surface shadow-sm overflow-hidden">
            <div className="bg-muted/30 px-6 py-4 border-b">
              <h2 className="font-serif font-semibold text-secondary">Resolve Open Escalation</h2>
            </div>
            <div className="p-6">
              <EscalationResolveForm />
            </div>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}
