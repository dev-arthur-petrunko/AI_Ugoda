"use client";

import { useEffect, useState } from "react";
import { Logo } from "./logo";

export function Loader() {
  const [show, setShow] = useState(true);

  useEffect(() => {
    const timer = setTimeout(() => setShow(false), 1800);
    return () => clearTimeout(timer);
  }, []);

  if (!show) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex flex-col items-center justify-center bg-obsidian text-cream"
      style={{ backgroundColor: "var(--bg)" }}
    >
      <div className="relative mb-6">
        <Logo className="w-24 h-24 md:w-32 md:h-32" />
        <div className="absolute inset-0 bg-[linear-gradient(135deg,#8F6F2B_0%,#E8C871_45%,#C9A24B_60%,#6E5420_100%)] opacity-0 animate-[shimmer_2s_ease-in-out_infinite] rounded-full" />
      </div>
      <p className="text-sm text-cream-muted tracking-wider">AI Ugoda</p>
      <p className="text-xs text-cream-muted/60 mt-1">Навигатор і детектор небезпеки над законодавством України</p>
    </div>
  );
}