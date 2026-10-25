"use client";

import { ReactNode } from "react";
import { Card, CardContent } from "@/components/ui/card";

interface EmptyStateProps {
  icon: ReactNode;
  title: string;
  description: string;
  actionLabel?: string;
  actionHref?: string;
}

export function EmptyState({ icon, title, description, actionLabel, actionHref }: EmptyStateProps) {
  return (
    <Card className="flex flex-col items-center justify-center py-12 text-text-secondary">
      <div className="mb-4 h-12 w-12 rounded-md bg-elevated flex items-center justify-center text-gold-muted opacity-60">
        {icon}
      </div>
      <h3 className="text-sm font-medium text-text">{title}</h3>
      <p className="text-xs text-text-secondary/60 mt-1 max-w-xs text-center">{description}</p>
      {actionLabel && actionHref && (
        <a href={actionHref} className="mt-4 text-xs text-gold hover:underline">
          {actionLabel}
        </a>
      )}
    </Card>
  );
}