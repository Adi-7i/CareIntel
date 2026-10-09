import * as React from "react";
import type { Metadata } from "next";
import { CaseDetails } from "@/components/cases/case-details";

export const metadata: Metadata = {
  title: "Case Details | CareIntel",
  description: "View and manage clinical case details",
};

export default function CaseDetailsPage() {
  return (
    <div className="max-w-6xl mx-auto py-2">
      <CaseDetails />
    </div>
  );
}
