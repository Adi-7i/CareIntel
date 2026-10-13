import * as React from "react";
import type { Metadata } from "next";
import { CaseDetails } from "@/components/cases/case-details";

export const metadata: Metadata = {
  title: "Case Details | CareIntel",
  description: "View and manage clinical case details",
};

interface CaseDetailsPageProps {
  params: Promise<{ id: string }>;
}

export default async function CaseDetailsPage({ params }: CaseDetailsPageProps) {
  const { id } = await params;
  return (
    <div className="max-w-6xl mx-auto py-2">
      <CaseDetails caseId={id} />
    </div>
  );
}
