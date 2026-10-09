import * as React from "react";
import type { Metadata } from "next";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { TextEvidenceForm } from "@/components/evidence/text-evidence-form";
import { FileEvidenceForm } from "@/components/evidence/file-evidence-form";
import { EvidenceMetadataCard } from "@/components/evidence/evidence-metadata-card";
import { TaskStatusPanel } from "@/components/evidence/task-status-panel";
import { ProcessingTriggerForm } from "@/components/evidence/processing-trigger-form";

export const metadata: Metadata = {
  title: "Evidence & Document Workspace | CareIntel",
  description: "Manage clinical evidence and document processing workflows",
};

export default function EvidencePage() {
  return (
    <div className="space-y-6 max-w-6xl mx-auto py-2">
      <header>
        <h1 className="font-serif text-3xl font-semibold tracking-tight text-secondary">
          Evidence Workspace
        </h1>
        <p className="mt-1 font-serif text-sm text-muted-foreground">
          Intake, review, and process clinical evidence and documentation.
        </p>
      </header>
      
      <div className="rounded-md bg-muted/40 border p-4 mb-6">
        <p className="font-serif text-sm text-secondary font-semibold mb-1">
          System Integration Notice
        </p>
        <p className="font-serif text-sm text-muted-foreground">
          This workspace is prepared for backend integration. Evidence operations cannot be executed until the authenticated session and backend connection are established. The evidence list is intentionally omitted as no such endpoint exists in the current system.
        </p>
      </div>

      <Tabs defaultValue="submit" className="w-full">
        <TabsList className="mb-4">
          <TabsTrigger value="submit">Submit Evidence</TabsTrigger>
          <TabsTrigger value="record">Evidence Record</TabsTrigger>
          <TabsTrigger value="processing">Processing & Tasks</TabsTrigger>
        </TabsList>
        
        <TabsContent value="submit" className="space-y-8">
          <div className="border rounded-lg bg-surface shadow-sm overflow-hidden">
            <div className="bg-muted/30 px-6 py-4 border-b">
              <h2 className="font-serif font-semibold text-secondary">File Upload</h2>
            </div>
            <div className="p-6">
              <FileEvidenceForm />
            </div>
          </div>
          
          <div className="border rounded-lg bg-surface shadow-sm overflow-hidden">
            <div className="bg-muted/30 px-6 py-4 border-b">
              <h2 className="font-serif font-semibold text-secondary">Text Registration</h2>
            </div>
            <div className="p-6">
              <TextEvidenceForm />
            </div>
          </div>
        </TabsContent>
        
        <TabsContent value="record">
          <EvidenceMetadataCard />
        </TabsContent>
        
        <TabsContent value="processing" className="space-y-8">
          <div className="border rounded-lg bg-surface shadow-sm overflow-hidden">
            <div className="bg-muted/30 px-6 py-4 border-b">
              <h2 className="font-serif font-semibold text-secondary">Trigger Pipeline</h2>
            </div>
            <div className="p-6">
              <ProcessingTriggerForm />
            </div>
          </div>
          
          <TaskStatusPanel />
        </TabsContent>
      </Tabs>
    </div>
  );
}
