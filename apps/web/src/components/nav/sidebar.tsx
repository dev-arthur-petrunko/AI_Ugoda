"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { LayoutDashboard, Search, Clock, FileCheck, BarChart3, ShieldAlert, Link as LinkIcon, Eye, Folder, Upload, Settings, ChevronLeft, Menu, LogOut } from "lucide-react";
import { Button } from "@/components/ui/button";

const navItems = [
  { name: "Огляд", href: "/uk/dashboard", icon: LayoutDashboard },
  { name: "Пошук законодавства", href: "/uk/legislation", icon: Search },
  { name: "Нові закони та зміни", href: "/uk/changes", icon: Clock },
  { name: "Аналіз договорів", href: "/uk/contracts", icon: FileCheck },
  { name: "AI Юрист-дослідник", href: "/uk/assistant", icon: BarChart3 },
  { name: "Протиріччя та колізії", href: "/uk/conflicts", icon: ShieldAlert },
  { name: "Карта законодавства", href: "/uk/legal-map", icon: LinkIcon },
  { name: "Моніторинг", href: "/uk/monitoring", icon: Eye },
  { name: "Мої документи", href: "/uk/workspace", icon: Folder },
  { name: "Звіти", href: "/uk/reports", icon: Upload },
  { name: "Налаштування", href: "/uk/settings", icon: Settings },
];
const adminItems = [{ name: "Панель адміністратора", href: "/uk/admin", icon: ShieldAlert }];

function cls(...c: (string | boolean | undefined | null)[]) { return c.filter(Boolean).join(" "); }

export function Sidebar({ collapsed }: { collapsed: boolean }) {
  const pathname = usePathname();
  const [hovered, setHovered] = useState<string | null>(null);

  return (
    <aside className="fixed left-0 top-0 z-40 h-screen border-r border-gold/10 bg-sidebar transition-all duration-300" style={{ width: collapsed ? 64 : 260 }} onMouseEnter={() => setHovered("expand")} onMouseLeave={() => setHovered(null)}>
      <div className="flex h-full flex-col">
        <div className="flex h-16 items-center justify-between border-b border-gold/10 px-4 shrink-0">
          <Link href="/uk/dashboard" className="flex items-center gap-2.5">
            <span className="block h-3 w-3 rounded-full bg-gold animate-pulse" />
            <span className={collapsed ? "sr-only" : "text-lg font-bold text-gold-bright tracking-tight"}>AI Ugoda</span>
          </Link>
          {!collapsed && (
            <button className="rounded-md p-1.5 text-text-secondary hover:text-gold hover:bg-elevated" aria-label="Згорнути навігацію">
              <ChevronLeft className="h-5 w-5" />
            </button>
          )}
        </div>

        <nav className="flex-1 overflow-y-auto px-2 py-4 space-y-1">
          <div className="mx-4 mb-2 mt-2 text-xs font-semibold text-text-secondary/70 uppercase tracking-wider">Розділи</div>
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = pathname === item.href;
            return (
              <Link key={item.href} href={item.href} onMouseEnter={() => setHovered(item.href)} onMouseLeave={() => setHovered(null)}
                className={cls("flex w-full items-center gap-3 rounded-md px-3 py-2.5 text-sm transition-colors", isActive ? "bg-gold/10 text-gold-bright border-r-2 border-gold" : "text-text-secondary/80 hover:bg-elevated hover:text-text")}>
                <Icon className={cls("h-5 w-5 shrink-0", isActive ? "text-gold" : "text-text-secondary/70")} />
                {(collapsed || hovered !== item.href) && <span className="truncate">{item.name}</span>}
              </Link>
            );
          })}

          <div className="mx-4 mb-2 mt-6 text-xs font-semibold text-text-secondary/70 uppercase tracking-wider">Адміністрування</div>
          {adminItems.map((item) => {
            const Icon = item.icon;
            const isActive = pathname === item.href;
            return (
              <Link key={item.href} href={item.href} onMouseEnter={() => setHovered(item.href)} onMouseLeave={() => setHovered(null)}
                className={cls("flex w-full items-center gap-3 rounded-md px-3 py-2.5 text-sm transition-colors", isActive ? "bg-error/10 text-error border-r-2 border-error" : "text-text-secondary/60 hover:bg-elevated hover:text-text")}>
                <Icon className={cls("h-5 w-5 shrink-0", isActive ? "text-error" : "text-text-secondary/60")} />
                {(collapsed || hovered !== item.href) && <span className="truncate">{item.name}</span>}
              </Link>
            );
          })}
        </nav>

        <div className="border-t border-gold/10 px-4 py-4 shrink-0">
          <button className="flex w-full items-center gap-3 rounded-md px-3 py-2.5 text-sm text-text-secondary hover:text-text hover:bg-elevated transition-colors">
            <LogOut className="h-5 w-5 shrink-0 text-text-secondary/70" /><span>Вийти</span>
          </button>
        </div>
      </div>

      {collapsed && (
        <AnimatePresence>
          <motion.div initial={{ opacity: 0, x: -10 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -10 }}
            className="absolute left-0 top-0 z-50 h-screen w-24 translate-x-full bg-sidebar border-r border-gold/10 flex flex-col">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = pathname === item.href;
              return (
                <Button key={item.href} asChild variant="ghost" className={cls("flex flex-col items-center gap-1.5 rounded-md p-2.5 transition-colors w-full", isActive ? "bg-gold/10 text-gold-bright" : "text-text-secondary/60 hover:bg-elevated hover:text-text")}>
                  <Link href={item.href}><Icon className="h-5 w-5" /></Link>
                  <span className="text-xs">{item.name}</span>
                </Button>
              );
            })}
          </motion.div>
        </AnimatePresence>
      )}
    </aside>
  );
}

export function MobileSidebarTrigger() {
  return (
    <button className="mr-2 flex items-center gap-2 rounded-md p-1.5 text-text-secondary hover:text-gold hover:bg-elevated md:hidden" aria-label="Розкрити меню">
      <Menu className="h-5 w-5" />
    </button>
  );
}