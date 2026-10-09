import * as React from "react";

export function BrandPanel() {
  return (
    <div className="relative hidden w-full flex-col justify-between overflow-hidden bg-gradient-to-br from-[var(--ci-navy-900)] to-[var(--ci-navy-800)] p-10 text-[var(--login-brand-text)] md:flex md:w-[45%] lg:w-[45%] xl:w-[40%]">
      {/* Brand Header */}
      <div className="relative z-20">
        <h1 className="font-serif text-2xl font-semibold tracking-tight text-white">
          CareIntel
        </h1>
      </div>

      {/* Main Copy */}
      <div className="relative z-20 mt-auto mb-16 max-w-[320px]">
        <h2 className="mb-4 font-serif text-3xl font-semibold leading-tight text-white">
          Secure access to your clinical workspace
        </h2>
        <p className="font-serif text-base text-[var(--login-brand-muted)] leading-relaxed">
          Integrated intelligence and structured workflows for healthcare teams.
        </p>
      </div>

      {/* Abstract Motif (Geometric Nodes) */}
      <div className="pointer-events-none absolute inset-0 z-10 overflow-hidden">
        <svg
          className="absolute -right-[15%] -bottom-[10%] h-[120%] w-[120%] opacity-15"
          viewBox="0 0 800 800"
          xmlns="http://www.w3.org/2000/svg"
        >
          <g strokeWidth="2" fill="none" stroke="currentColor">
            {/* Base grid / connecting lines */}
            <path d="M100,700 L300,500 L500,600 L700,300" stroke="var(--ci-teal-700)" strokeWidth="4" />
            <path d="M200,800 L300,500 L600,200" stroke="var(--ci-aqua)" strokeWidth="2" strokeDasharray="6 6" />
            
            {/* Node 1 */}
            <circle cx="300" cy="500" r="16" fill="var(--ci-navy-900)" stroke="var(--ci-aqua)" strokeWidth="4" />
            <circle cx="300" cy="500" r="48" stroke="var(--ci-teal-700)" opacity="0.5" />
            
            {/* Node 2 */}
            <circle cx="500" cy="600" r="12" fill="var(--ci-teal-700)" stroke="none" />
            <circle cx="500" cy="600" r="32" stroke="var(--ci-aqua)" opacity="0.3" />
            
            {/* Node 3 */}
            <circle cx="700" cy="300" r="24" fill="var(--ci-navy-800)" stroke="var(--ci-teal-700)" strokeWidth="4" />
            <circle cx="700" cy="300" r="72" stroke="var(--ci-aqua)" strokeDasharray="4 8" opacity="0.4" />
            
            {/* Decorative arcs */}
            <path d="M150,500 A 150 150 0 0 1 300,350" stroke="var(--ci-teal-700)" opacity="0.4" />
            <path d="M500,450 A 150 150 0 0 1 650,600" stroke="var(--ci-aqua)" opacity="0.2" />
          </g>
        </svg>
      </div>
    </div>
  );
}
