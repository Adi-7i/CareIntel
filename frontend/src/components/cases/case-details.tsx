"use client";

import * as React from "react";
import Link from "next/link";
import { ArrowLeft, Clock, ShieldCheck, Activity } from "lucide-react";
import { Button } from "@/components/ui/button";
import { EmptyState } from "@/components/ui/empty-state";
import { StatusBadge } from "./status-badge";

export function CaseDetails() {
  return (
    <div className="space-y-6 max-w-6xl mx-auto">
      {/* Header Area */}
      <div className="flex items-center gap-4 border-b pb-4">
        <Button render={<Link href="/cases" />} variant="outline" size="icon" aria-label="Back to cases">
          <ArrowLeft className="size-4" />
        </Button>
        <div className="flex-1">
          <div className="flex items-center gap-3">
            <h1 className="font-serif text-2xl font-semibold tracking-tight text-secondary">
              Case Details Workspace
            </h1>
            <StatusBadge status="Under Review" />
          </div>
          <p className="font-serif text-sm text-muted-foreground mt-1">
            Case information and timeline will populate when connected.
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main Workspace (Left Column) */}
        <div className="lg:col-span-2 space-y-6">
          <div className="border rounded-lg bg-surface shadow-sm overflow-hidden">
            <div className="bg-muted/30 px-6 py-4 border-b">
              <h2 className="font-serif font-semibold text-secondary flex items-center gap-2">
                <Activity className="size-4" />
                Case Overview
              </h2>
            </div>
            <div className="p-6">
              <EmptyState 
                icon={<Activity className="size-8" />} 
                title="No Data Available" 
                description="The case overview relies on backend integration to display clinical summaries and identifiers." 
              />
            </div>
          </div>

          <div className="border rounded-lg bg-surface shadow-sm overflow-hidden">
            <div className="bg-muted/30 px-6 py-4 border-b">
              <h2 className="font-serif font-semibold text-secondary flex items-center gap-2">
                <Clock className="size-4" />
                Encounter History & Timeline
              </h2>
            </div>
            <div className="p-6">
              <EmptyState 
                icon={<Clock className="size-8" />} 
                title="Timeline Disconnected" 
                description="Historical events, evidence ingestion, and state transitions will be rendered here." 
              />
            </div>
          </div>
        </div>

        {/* Context Column (Right Column) */}
        <div className="space-y-6">
          <div className="border rounded-lg bg-surface shadow-sm overflow-hidden">
            <div className="bg-muted/30 px-6 py-4 border-b">
              <h2 className="font-serif font-semibold text-secondary flex items-center gap-2">
                <ShieldCheck className="size-4" />
                Consent Status
              </h2>
            </div>
            <div className="p-6">
              <EmptyState 
                icon={<ShieldCheck className="size-8" />} 
                title="Consent Unverified" 
                description="Active data processing consent status requires backend validation." 
              />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
