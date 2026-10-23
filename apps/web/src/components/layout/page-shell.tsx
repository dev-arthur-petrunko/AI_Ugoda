"use client";

import { ReactNode } from "react";

interface PageShellProps {
  title: string;
  subtitle?: string;
  children: ReactNode;
}

export function PageShell({ title, subtitle, children }: PageShellProps) {
  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-2xl font-bold text-text tracking-tight">{title}</h1>
        {subtitle && <p className="text-text-secondary">{subtitle}</p>}
      </div>
      <div className="border-t border-gold/10 pt-4">{children}</div>
    </div>
  );
}