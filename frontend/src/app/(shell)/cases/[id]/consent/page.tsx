import * as React from "react";
import type { Metadata } from "next";
import { ConsentPanel } from "@/components/cases/consent-panel";

export const metadata: Metadata = {
  title: "Case Consent | CareIntel",
  description: "View and verify subject consent purposes and notice versions",
};

interface CaseConsentPageProps {
  params: Promise<{ id: string }>;
}

export default async function CaseConsentPage({ params }: CaseConsentPageProps) {
  const { id } = await params;
  return (
    <div className="max-w-6xl mx-auto py-2">
      <ConsentPanel caseId={id} />
    </div>
  );
}
