import * as React from "react";
import type { Metadata } from "next";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { ReferralPrepareForm } from "@/components/handoff/referral-prepare-form";
import { ReferralFinalizeForm } from "@/components/handoff/referral-finalize-form";
import { HandoffInitiateForm } from "@/components/handoff/handoff-initiate-form";
import { HandoffSendForm } from "@/components/handoff/handoff-send-form";
import { HandoffAcknowledgeForm } from "@/components/handoff/handoff-acknowledge-form";
import { HandoffCompleteForm } from "@/components/handoff/handoff-complete-form";
import { RecipientPanel } from "@/components/handoff/recipient-panel";

export const metadata: Metadata = {
  title: "Referral & Handoff | CareIntel",
  description: "Manage referral packages and handoff lifecycles.",
};

export default function HandoffPage() {
  return (
    <div className="space-y-6 max-w-6xl mx-auto py-2">
      <header>
        <h1 className="font-serif text-3xl font-semibold tracking-tight text-secondary">
          Referral & Handoff
        </h1>
        <p className="mt-1 font-serif text-sm text-muted-foreground">
          Prepare clinical referral packages and manage the delivery lifecycle.
        </p>
      </header>
      
      <div className="rounded-md bg-muted/40 border p-4 mb-6">
        <p className="font-serif text-sm text-secondary font-semibold mb-1">
          System Integration Notice
        </p>
        <p className="font-serif text-sm text-muted-foreground">
          This workspace is prepared for backend integration. Forms validate locally but require an active session and connected backend services. No data is fabricated. Referral listing is not supported by the backend schema.
        </p>
      </div>

      <Tabs defaultValue="referral" className="w-full">
        <TabsList className="mb-4">
          <TabsTrigger value="referral">Referral Packaging</TabsTrigger>
          <TabsTrigger value="lifecycle">Handoff Lifecycle</TabsTrigger>
          <TabsTrigger value="recipients">Recipients</TabsTrigger>
        </TabsList>
        
        <TabsContent value="referral" className="space-y-8">
          <div className="border rounded-lg bg-surface shadow-sm overflow-hidden">
            <div className="bg-muted/30 px-6 py-4 border-b">
              <h2 className="font-serif font-semibold text-secondary">Prepare Package</h2>
            </div>
            <div className="p-6">
              <ReferralPrepareForm />
            </div>
          </div>
          
          <div className="border rounded-lg bg-surface shadow-sm overflow-hidden">
            <div className="bg-muted/30 px-6 py-4 border-b">
              <h2 className="font-serif font-semibold text-secondary">Finalize Package</h2>
            </div>
            <div className="p-6">
              <ReferralFinalizeForm />
            </div>
          </div>
        </TabsContent>
        
        <TabsContent value="lifecycle" className="space-y-8">
          <div className="border rounded-lg bg-surface shadow-sm overflow-hidden">
            <div className="bg-muted/30 px-6 py-4 border-b">
              <h2 className="font-serif font-semibold text-secondary">1. Initiate Handoff</h2>
            </div>
            <div className="p-6">
              <HandoffInitiateForm />
            </div>
          </div>

          <div className="border rounded-lg bg-surface shadow-sm overflow-hidden">
            <div className="bg-muted/30 px-6 py-4 border-b">
              <h2 className="font-serif font-semibold text-secondary">2. Send Handoff</h2>
            </div>
            <div className="p-6">
              <HandoffSendForm />
            </div>
          </div>

          <div className="border rounded-lg bg-surface shadow-sm overflow-hidden">
            <div className="bg-muted/30 px-6 py-4 border-b">
              <h2 className="font-serif font-semibold text-secondary">3. Acknowledge Handoff</h2>
            </div>
            <div className="p-6">
              <HandoffAcknowledgeForm />
            </div>
          </div>

          <div className="border rounded-lg bg-surface shadow-sm overflow-hidden">
            <div className="bg-muted/30 px-6 py-4 border-b">
              <h2 className="font-serif font-semibold text-secondary">4. Complete Handoff</h2>
            </div>
            <div className="p-6">
              <HandoffCompleteForm />
            </div>
          </div>
        </TabsContent>
        
        <TabsContent value="recipients">
          <RecipientPanel />
        </TabsContent>
      </Tabs>
    </div>
  );
}
