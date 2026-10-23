"use client";

import { useState } from "react";
import { Sidebar } from "@/components/nav/sidebar";
import { Topbar } from "@/components/nav/topbar";

export default function LocaleLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const [collapsed, setCollapsed] = useState(false);

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-bg text-text">
      <Sidebar collapsed={collapsed} />
      <div className="flex flex-col flex-1 relative ml-0 transition-all duration-300" style={{ marginLeft: collapsed ? 64 : 260 }}>
        <Topbar onMenuToggle={() => setCollapsed(!collapsed)} />
        <main className="flex-1 overflow-y-auto bg-bg p-4 md:p-6 lg:p-8">{children}</main>
      </div>
    </div>
  );
}