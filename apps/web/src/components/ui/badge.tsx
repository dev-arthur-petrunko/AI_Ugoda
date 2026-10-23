"use client";

import * as React from "react";
import { cn } from "@/lib/utils";

const badgeVariants = (
  variant?: "default" | "secondary" | "destructive" | "outline" | "gold" | "muted",
) =>
  cn(
    "inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2",
    {
      default: "border-transparent bg-primary text-primary-foreground hover:bg-primary/80",
      secondary: "border-transparent bg-secondary text-secondary-foreground hover:bg-secondary/80",
      destructive:
        "border-transparent bg-destructive text-destructive-foreground hover:bg-destructive/80",
      outline: "border-input bg-background hover:bg-accent hover:text-accent-foreground",
      gold: "border-gold/30 bg-gold/10 text-gold border",
      muted: "border-transparent bg-elevated text-text-secondary",
    },
    variant,
  );

interface BadgeProps
  extends React.HTMLAttributes<HTMLDivElement> {
  variant?: "default" | "secondary" | "destructive" | "outline" | "gold" | "muted";
}

const Badge = React.forwardRef<HTMLDivElement, BadgeProps>(({ className, variant, ...props }, ref) => (
  <div ref={ref} className={cn(badgeVariants(variant), className)} {...props} />
));
Badge.displayName = "Badge";

export { Badge, badgeVariants };