import * as React from "react";
import type { Metadata } from "next";
import { CaseForm } from "@/components/cases/case-form";

export const metadata: Metadata = {
  title: "Create Case | CareIntel",
  description: "Initialize a new clinical case",
};

export default function NewCasePage() {
  return (
    <div className="max-w-6xl mx-auto py-2">
      <CaseForm />
    </div>
  );
}
