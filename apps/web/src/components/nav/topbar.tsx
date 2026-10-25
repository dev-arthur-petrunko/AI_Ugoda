"use client";

import { Search, Bell, Circle, ChevronDown } from "lucide-react";
import { MobileSidebarTrigger } from "./sidebar";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

export function Topbar({ onMenuToggle }: { onMenuToggle: () => void }) {
  return (
    <header className="sticky top-0 z-30 flex h-16 items-center justify-between border-b border-gold/10 bg-sidebar/95 backdrop-blur-[22px] px-4">
      <div className="flex items-center gap-3">
        <MobileSidebarTrigger />
        <div className="hidden md:flex w-[420px]">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-text-secondary/60" />
            <Input
              placeholder="Пошук законодавства…"
              className="pl-10 pr-4 w-full"
            />
          </div>
        </div>
      </div>

      <div className="flex items-center gap-3">
        <div className="hidden md:flex flex-col items-end gap-0.5">
          <span className="text-xs text-text-secondary">Остання синхронізація</span>
          <span className="text-xs font-mono text-gold-bright">Сьогодні, 10:24</span>
        </div>
        <div className="flex items-center gap-2">
          <button className="relative p-1.5 text-text-secondary hover:text-gold" aria-label="Сповіщення">
            <Bell className="h-5 w-5" />
          </button>
          <div className="flex items-center gap-2 rounded-md border border-gold/20 bg-elevated px-3 py-1.5">
            <div className="h-2 w-2 rounded-full bg-success" />
            <span className="text-xs text-text-secondary">Онлайн</span>
            <ChevronDown className="h-3 w-3 text-text-secondary/50" />
          </div>
        </div>
      </div>
    </header>
  );
}