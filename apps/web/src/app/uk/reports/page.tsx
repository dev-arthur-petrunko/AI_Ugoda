"use client";

import { useEffect, useState } from "react";
import { PageShell } from "@/components/layout/page-shell";
import { getStats } from "@/lib/api";
import { BarChart3 } from "lucide-react";

type Stats = { documents: number; revisions: number; provisions: number; links: number };

export default function ReportsPage() {
  const [stats, setStats] = useState<Stats | null>(null);
  const [state, setState] = useState<"loading" | "ready" | "error">("loading");
  const [errMsg, setErrMsg] = useState<string | null>(null);

  const load = () => {
    setState("loading");
    getStats()
      .then((s) => {
        setStats(s);
        setState("ready");
      })
      .catch((e: any) => {
        setErrMsg(e?.message || "Немає зв'язку з сервером");
        setState("error");
      });
  };

  useEffect(load, []);

  const cards: [string, number | string, string][] = stats
    ? [
        ["Актів у базі", stats.documents, "legal_documents"],
        ["Редакцій", stats.revisions, "document_revisions"],
        ["Статей та положень", stats.provisions, "legal_provisions"],
        ["Звʼязків між нормами", stats.links, "legal_links"],
      ]
    : [];

  return (
    <PageShell
      title="Звіти"
      subtitle="Агреговані показники бази законодавства та роботи системи."
    >
      <div className="space-y-4">
        {state === "loading" && <p className="text-text-secondary">Завантаження…</p>}
        {state === "error" && (
          <div className="glass card text-center py-8">
            <p className="text-red-400 text-sm">{errMsg}</p>
            <button className="btn s" style={{ marginTop: 10 }} onClick={load}>
              Повторити
            </button>
          </div>
        )}
        {state === "ready" && (
          <>
            <div className="grid" style={{ gridTemplateColumns: "repeat(auto-fill, minmax(200px, 1fr))" }}>
              {cards.map(([label, value, table]) => (
                <div key={table} className="glass card">
                  <BarChart3 className="h-4 w-4 mb-2 text-text-secondary" />
                  <p className="text-2xl font-medium">{value}</p>
                  <p className="text-sm text-text-secondary">{label}</p>
                  <p className="tag mt-1">джерело: {table}</p>
                </div>
              ))}
            </div>
            <div className="glass card">
              <p className="tag">
                Звіти за періоди, договори та експорт у PDF/CSV додаються на етапі, коли зʼявиться
                періодична агрегація та черга розрахунків.
              </p>
            </div>
          </>
        )}
      </div>
    </PageShell>
  );
}
