"use client";

import * as React from "react";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { FormError } from "@/components/auth/form-error";
import { ArrowLeft } from "lucide-react";
import { BrandPanel } from "@/components/auth/brand-panel";

export default function ForgotPasswordPage() {
  const [email, setEmail] = React.useState("");
  const [error, setError] = React.useState<string | undefined>();
  const [submitted, setSubmitted] = React.useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!email) {
      setError("Email is required.");
      return;
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      setError("Please enter a valid email address.");
      return;
    }
    setError(undefined);
    setSubmitted(true);
  };

  return (
    <div className="flex min-h-screen w-full flex-col md:flex-row">
      {/* Mobile Brand Header */}
      <div className="flex h-16 w-full items-center bg-[var(--ci-navy-900)] px-6 md:hidden">
        <span className="font-serif text-xl font-semibold tracking-tight text-white">
          CareIntel
        </span>
      </div>

      <BrandPanel />

      <div className="flex flex-1 items-center justify-center py-12 md:py-0">
        <div className="w-full max-w-[380px] mx-auto px-6 md:px-0">
          <div className="mb-8">
            <Link 
              href="/login" 
              className="inline-flex items-center text-sm font-medium text-muted-foreground hover:text-foreground mb-6"
            >
              <ArrowLeft className="mr-2 size-4" />
              Back to Sign In
            </Link>
            <h2 className="font-serif text-3xl font-semibold tracking-tight text-secondary">
              Reset Password
            </h2>
            <p className="mt-2 font-serif text-sm text-muted-foreground">
              Enter your email to receive password reset instructions.
            </p>
          </div>

          {submitted ? (
            <div className="rounded-md bg-[var(--status-info-surface)] p-6 border border-[var(--status-info-surface)] text-center">
              <h3 className="font-serif text-lg font-semibold text-[var(--status-info-text)] mb-2">
                Authentication Disconnected
              </h3>
              <p className="font-serif text-sm text-[var(--status-info-text)]">
                The form is validated locally, but no reset email has been sent. This feature will be functional after backend integration.
              </p>
              <Button render={<Link href="/login" />} variant="outline" className="mt-6 w-full font-serif">
                Return to Sign In
              </Button>
            </div>
          ) : (
            <form onSubmit={handleSubmit} className="space-y-6">
              <div className="space-y-2">
                <Label htmlFor="email" className={error ? "text-destructive" : ""}>
                  Email Address
                </Label>
                <Input
                  id="email"
                  type="email"
                  placeholder="name@example.com"
                  value={email}
                  onChange={(e) => {
                    setEmail(e.target.value);
                    if (error) setError(undefined);
                  }}
                  aria-invalid={!!error}
                  aria-describedby={error ? "email-error" : undefined}
                  className={error ? "border-destructive focus-visible:ring-destructive/50" : ""}
                />
                <FormError id="email-error" message={error} />
              </div>

              <Button type="submit" className="w-full font-serif text-base h-11">
                Send Instructions
              </Button>
            </form>
          )}
        </div>
      </div>
    </div>
  );
}
