"use client";

import * as React from "react";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { FormError } from "./form-error";
import { PasswordField } from "./password-field";

interface FormState {
  status: "idle" | "submitting" | "unconnected";
  errors: {
    email?: string;
    password?: string;
  };
}

export function LoginForm() {
  const [state, setState] = React.useState<FormState>({
    status: "idle",
    errors: {},
  });

  const [email, setEmail] = React.useState("");
  const [password, setPassword] = React.useState("");

  const validate = () => {
    const errors: FormState["errors"] = {};
    if (!email) {
      errors.email = "Email is required.";
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      errors.email = "Please enter a valid email address.";
    }

    if (!password) {
      errors.password = "Password is required.";
    }

    return errors;
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (state.status === "submitting") return;

    const errors = validate();
    if (Object.keys(errors).length > 0) {
      setState({ status: "idle", errors });
      return;
    }

    // Simulate validation passing
    setState({ status: "submitting", errors: {} });

    // Transition to unconnected state
    setTimeout(() => {
      setState({ status: "unconnected", errors: {} });
    }, 1000);
  };

  return (
    <div className="w-full max-w-[380px] mx-auto px-6 md:px-0">
      <div className="mb-8">
        <h2 className="font-serif text-3xl font-semibold tracking-tight text-secondary">
          Sign in to CareIntel
        </h2>
        <p className="mt-2 font-serif text-sm text-muted-foreground">
          Enter your credentials to access the clinical workspace.
        </p>
      </div>

      {state.status === "unconnected" && (
        <div className="mb-6 rounded-md bg-[var(--status-info-surface)] p-4 border border-[var(--status-info-surface)]">
          <p className="font-serif text-sm text-[var(--status-info-text)]">
            <strong>Authentication disconnected.</strong><br />
            This form is validated locally but not wired to a backend.
          </p>
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-6" aria-label="Sign in to CareIntel">
        <div className="space-y-2">
          <Label htmlFor="email" className={state.errors.email ? "text-destructive" : ""}>
            Email Address
          </Label>
          <Input
            id="email"
            type="email"
            placeholder="name@example.com"
            value={email}
            onChange={(e) => {
              setEmail(e.target.value);
              if (state.errors.email) setState({ ...state, errors: { ...state.errors, email: undefined } });
            }}
            aria-invalid={!!state.errors.email}
            aria-describedby={state.errors.email ? "email-error" : undefined}
            disabled={state.status === "submitting"}
            className={state.errors.email ? "border-destructive focus-visible:ring-destructive/50" : ""}
          />
          <FormError id="email-error" message={state.errors.email} />
        </div>

        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <Label htmlFor="password" className={state.errors.password ? "text-destructive" : ""}>
              Password
            </Label>
            <Link
              href="/login/forgot-password"
              className="font-serif text-sm font-medium text-primary hover:underline"
              tabIndex={state.status === "submitting" ? -1 : 0}
            >
              Forgot password?
            </Link>
          </div>
          <PasswordField
            id="password"
            value={password}
            onChange={(e) => {
              setPassword(e.target.value);
              if (state.errors.password) setState({ ...state, errors: { ...state.errors, password: undefined } });
            }}
            aria-invalid={!!state.errors.password}
            aria-describedby={state.errors.password ? "password-error" : undefined}
            disabled={state.status === "submitting"}
            className={state.errors.password ? "border-destructive focus-visible:ring-destructive/50" : ""}
          />
          <FormError id="password-error" message={state.errors.password} />
        </div>

        <Button
          type="submit"
          className="w-full font-serif text-base h-11"
          disabled={state.status === "submitting"}
          aria-busy={state.status === "submitting"}
        >
          {state.status === "submitting" ? "Signing in..." : "Sign In"}
        </Button>
      </form>
    </div>
  );
}
