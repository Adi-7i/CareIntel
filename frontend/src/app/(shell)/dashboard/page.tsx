import * as React from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

export default function OverviewPage() {
  return (
    <div className="space-y-6 max-w-5xl">
      <header>
        <h1 className="font-serif text-3xl font-semibold text-secondary tracking-tight">Overview</h1>
        <p className="text-muted-foreground mt-1 text-sm">Application shell overview and navigation anchor.</p>
      </header>

      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        <Card>
          <CardHeader>
            <CardTitle>Welcome to CareIntel</CardTitle>
            <CardDescription>Shell navigation context</CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-foreground leading-relaxed">
              This surface demonstrates the main application layout, including responsive sidebar behavior, persistent header, and routing structure. No clinical data is presented in this phase.
            </p>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
