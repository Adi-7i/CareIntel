import * as React from "react";
import type { Metadata } from "next";
import { BrandPanel } from "@/components/auth/brand-panel";
import { LoginForm } from "@/components/auth/login-form";

export const metadata: Metadata = {
  title: "Sign In | CareIntel",
  description: "Secure access to your clinical workspace",
};

export default function LoginPage() {
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
        <LoginForm />
      </div>
    </div>
  );
}
