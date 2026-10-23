"use client";

import * as React from "react";
import { cn } from "@/lib/utils";

interface SkeletonProps extends React.HTMLAttributes<HTMLDivElement> {
  className?: string;
}

const Skeleton = React.forwardRef<HTMLDivElement, SkeletonProps>(({ className, ...props }, ref) => (
  <div
    ref={ref}
    role="status"
    aria-label="Завантаження…"
    className={cn("animate-pulse rounded-md bg-elevated", className)}
    {...props}
  />
));
Skeleton.displayName = "Skeleton";

export { Skeleton };