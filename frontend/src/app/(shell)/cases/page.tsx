import * as React from "react";
import type { Metadata } from "next";
import { CaseList } from "@/components/cases/case-list";

export const metadata: Metadata = {
  title: "Cases | CareIntel",
  description: "Manage clinical cases and workflows",
};

export default function CasesPage() {
  return (
    <div className="space-y-6 max-w-6xl mx-auto">
      <header>
        <h1 className="font-serif text-3xl font-semibold tracking-tight text-secondary">Cases</h1>
        <p className="mt-1 font-serif text-sm text-muted-foreground">
          Review, track, and manage clinical cases.
        </p>
      </header>

      <CaseList />
    </div>
  );
}
