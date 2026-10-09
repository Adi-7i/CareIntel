import * as React from "react";
import type { Metadata } from "next";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { ReviewQueueList } from "@/components/review/review-queue-list";
import { EnterQueueForm } from "@/components/review/enter-queue-form";
import { AssignReviewerForm } from "@/components/review/assign-reviewer-form";
import { ReassignReviewerForm } from "@/components/review/reassign-reviewer-form";
import { StartReviewForm } from "@/components/review/start-review-form";
import { ReviewWorkspacePanel } from "@/components/review/review-workspace-panel";
import { ReviewDecisionForm } from "@/components/review/review-decision-form";
import { DraftAcceptForm } from "@/components/review/draft-accept-form";
import { DraftRejectForm } from "@/components/review/draft-reject-form";
import { DraftEditForm } from "@/components/review/draft-edit-form";

export const metadata: Metadata = {
  title: "Review Workspace | CareIntel",
  description: "Manage clinical reviews, assignments, and AI draft decisions.",
};

export default function ReviewPage() {
  return (
    <div className="space-y-6 max-w-6xl mx-auto py-2">
      <header>
        <h1 className="font-serif text-3xl font-semibold tracking-tight text-secondary">
          Review Workspace
        </h1>
        <p className="mt-1 font-serif text-sm text-muted-foreground">
          Manage clinical review queues, assignments, and verify structured drafts.
        </p>
      </header>
      
      <div className="rounded-md bg-muted/40 border p-4 mb-6">
        <p className="font-serif text-sm text-secondary font-semibold mb-1">
          System Integration Notice
        </p>
        <p className="font-serif text-sm text-muted-foreground">
          This workspace is prepared for backend integration. Forms validate locally but require an active session and connected backend services. No data is fabricated.
        </p>
      </div>

      <Tabs defaultValue="queue" className="w-full">
        <TabsList className="mb-4">
          <TabsTrigger value="queue">Queue Management</TabsTrigger>
          <TabsTrigger value="actions">Review Actions</TabsTrigger>
          <TabsTrigger value="decision">Decision & Drafts</TabsTrigger>
        </TabsList>
        
        <TabsContent value="queue" className="space-y-8">
          <ReviewQueueList />
          
          <div className="border rounded-lg bg-surface shadow-sm overflow-hidden">
            <div className="bg-muted/30 px-6 py-4 border-b">
              <h2 className="font-serif font-semibold text-secondary">Enter Review Queue</h2>
            </div>
            <div className="p-6">
              <EnterQueueForm />
            </div>
          </div>
        </TabsContent>
        
        <TabsContent value="actions" className="space-y-8">
          <div className="border rounded-lg bg-surface shadow-sm overflow-hidden">
            <div className="bg-muted/30 px-6 py-4 border-b">
              <h2 className="font-serif font-semibold text-secondary">Start Review</h2>
            </div>
            <div className="p-6">
              <StartReviewForm />
            </div>
          </div>

          <div className="border rounded-lg bg-surface shadow-sm overflow-hidden">
            <div className="bg-muted/30 px-6 py-4 border-b">
              <h2 className="font-serif font-semibold text-secondary">Assign Reviewer</h2>
            </div>
            <div className="p-6">
              <AssignReviewerForm />
            </div>
          </div>

          <div className="border rounded-lg bg-surface shadow-sm overflow-hidden">
            <div className="bg-muted/30 px-6 py-4 border-b">
              <h2 className="font-serif font-semibold text-secondary">Reassign Reviewer</h2>
            </div>
            <div className="p-6">
              <ReassignReviewerForm />
            </div>
          </div>
        </TabsContent>
        
        <TabsContent value="decision" className="space-y-8">
          <ReviewWorkspacePanel />
          
          <div className="border rounded-lg bg-surface shadow-sm overflow-hidden">
            <div className="bg-muted/30 px-6 py-4 border-b">
              <h2 className="font-serif font-semibold text-secondary">Submit Review Decision</h2>
            </div>
            <div className="p-6">
              <ReviewDecisionForm />
            </div>
          </div>

          <div className="border rounded-lg bg-surface shadow-sm overflow-hidden">
            <div className="bg-muted/30 px-6 py-4 border-b">
              <h2 className="font-serif font-semibold text-secondary">Draft Modification Actions</h2>
            </div>
            <div className="p-6 space-y-6">
              <div className="border rounded-md p-4 bg-muted/20">
                <h3 className="font-serif font-semibold text-sm mb-4">Accept Draft</h3>
                <DraftAcceptForm />
              </div>
              <div className="border rounded-md p-4 bg-muted/20">
                <h3 className="font-serif font-semibold text-sm mb-4">Reject Draft</h3>
                <DraftRejectForm />
              </div>
              <div className="border rounded-md p-4 bg-muted/20">
                <h3 className="font-serif font-semibold text-sm mb-4">Edit Draft JSON</h3>
                <DraftEditForm />
              </div>
            </div>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}
